import os
import requests
import gradio as gr

API = os.getenv("BACKEND_URL", "").rstrip("/")
VIEWS = ["Perspective", "Front", "Rear", "Right Side", "Left Side", "Top", "Bottom"]
TIMEOUT = 180


def call(method, path, token=None, **kwargs):
    if not API:
        raise gr.Error("Backend URL is not configured. Set BACKEND_URL in this Space's Variables.")
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = requests.request(method, API + path, headers=headers, timeout=TIMEOUT, **kwargs)
    except requests.RequestException as exc:
        raise gr.Error(f"Cannot reach backend: {exc}")
    if not r.ok:
        try:
            body = r.json()
            message = body.get("error", {}).get("message") or body.get("detail") or r.text
        except Exception:
            message = r.text
        raise gr.Error(f"API {r.status_code}: {message}")
    return r


def auth(mode, name, email, password):
    if mode == "Register":
        data = call("POST", "/auth/register", json={"name": name, "email": email, "password": password}).json()
    else:
        data = call("POST", "/auth/login", json={"email": email, "password": password}).json()
    token = data["access_token"]
    user = data.get("user", {})
    projects = call("GET", "/projects", token).json()
    choices = [(f"{p['name']} (#{p['id']})", p["id"]) for p in projects]
    return token, f"Signed in as {user.get('name', email)}", gr.update(choices=choices, value=choices[0][1] if choices else None)


def refresh_projects(token):
    rows = call("GET", "/projects", token).json()
    choices = [(f"{p['name']} (#{p['id']})", p["id"]) for p in rows]
    return gr.update(choices=choices, value=choices[0][1] if choices else None), f"Loaded {len(rows)} project(s)."


def create_project(token, name, description):
    if not token:
        raise gr.Error("Sign in first.")
    call("POST", "/projects", token, json={"name": name, "description": description or ""})
    return refresh_projects(token)


def upload_view(token, project_id, view, file):
    if not token or not project_id:
        raise gr.Error("Sign in and select a project first.")
    if file is None:
        raise gr.Error("Choose an image first.")
    with open(file, "rb") as f:
        r = call("POST", f"/projects/{int(project_id)}/views/{view}", token,
                 files={"file": (os.path.basename(file), f, "application/octet-stream")})
    item = r.json()
    return f"Uploaded {view}: image #{item.get('id')} — {item.get('processing_status')}"


def process_project(token, project_id):
    if not token or not project_id:
        raise gr.Error("Sign in and select a project first.")
    data = call("POST", f"/ai/process/project/{int(project_id)}", token).json()
    return f"Processing request finished. Queued image IDs: {data.get('queued', [])}; skipped: {data.get('skipped', [])}."


def show_images(token, project_id):
    if not token or not project_id:
        raise gr.Error("Sign in and select a project first.")
    rows = call("GET", f"/projects/{int(project_id)}/images", token).json()
    return "\n".join([f"#{x['id']} · {x.get('view_type')} · {x.get('processing_status')} · approval: {x.get('approval_status')}" for x in rows]) or "No images uploaded yet."


def review(token, image_id, action):
    if not token or not image_id:
        raise gr.Error("Sign in and enter an image ID.")
    item = call("POST", f"/images/{int(image_id)}/review", token, json={"action": action}).json()
    return f"Image #{item['id']}: {item.get('processing_status')} / {item.get('approval_status')}"


def generate_pdf(token, project_id):
    if not token or not project_id:
        raise gr.Error("Sign in and select a project first.")
    result = call("POST", f"/projects/{int(project_id)}/documents", token).json()
    doc = result.get("document", {})
    doc_id = doc.get("id")
    if not doc_id:
        return str(result), None
    response = call("GET", f"/documents/{doc_id}/download", token)
    path = f"/tmp/patentvision-{doc_id}.pdf"
    with open(path, "wb") as f:
        f.write(response.content)
    return f"Generated document #{doc_id}.", path


with gr.Blocks(title="PatentVision AI", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 📐 PatentVision AI\nConvert product photographs into patent-style technical drawings and a 7-page representation PDF.\n\n**Demo notice:** data is temporary and can be erased when the backend Space restarts or rebuilds.")
    token_state = gr.State("")
    with gr.Tab("Account"):
        mode = gr.Radio(["Register", "Login"], value="Register", label="Action")
        name = gr.Textbox(label="Name (registration)")
        email = gr.Textbox(label="Email")
        password = gr.Textbox(label="Password", type="password")
        auth_btn = gr.Button("Continue", variant="primary")
        auth_status = gr.Markdown()
        project_dropdown = gr.Dropdown(label="Select project", choices=[])
        refresh_btn = gr.Button("Refresh projects")
    with gr.Tab("Projects"):
        project_name = gr.Textbox(label="Project name")
        project_description = gr.Textbox(label="Description", lines=2)
        create_btn = gr.Button("Create project", variant="primary")
        project_status = gr.Markdown()
    with gr.Tab("Upload & process"):
        view = gr.Dropdown(VIEWS, value="Front", label="Patent view")
        image_file = gr.File(label="Product photograph", file_types=["image"], type="filepath")
        upload_btn = gr.Button("Upload selected view")
        upload_status = gr.Markdown()
        process_btn = gr.Button("Process project", variant="primary")
        process_status = gr.Markdown()
        inspect_btn = gr.Button("Refresh image statuses")
        image_status = gr.Textbox(label="Uploaded images", lines=8)
    with gr.Tab("Review & PDF"):
        image_id = gr.Number(label="Image ID to review", precision=0)
        with gr.Row():
            approve_btn = gr.Button("Approve drawing")
            reject_btn = gr.Button("Reject drawing")
        review_status = gr.Markdown()
        pdf_btn = gr.Button("Generate 7-page patent PDF", variant="primary")
        pdf_status = gr.Markdown()
        pdf_file = gr.File(label="Generated PDF")

    auth_btn.click(auth, [mode, name, email, password], [token_state, auth_status, project_dropdown])
    refresh_btn.click(refresh_projects, [token_state], [project_dropdown, auth_status])
    create_btn.click(create_project, [token_state, project_name, project_description], [project_dropdown, project_status])
    upload_btn.click(upload_view, [token_state, project_dropdown, view, image_file], [upload_status])
    process_btn.click(process_project, [token_state, project_dropdown], [process_status])
    inspect_btn.click(show_images, [token_state, project_dropdown], [image_status])
    approve_btn.click(lambda t, i: review(t, i, "approve"), [token_state, image_id], [review_status])
    reject_btn.click(lambda t, i: review(t, i, "reject"), [token_state, image_id], [review_status])
    pdf_btn.click(generate_pdf, [token_state, project_dropdown], [pdf_status, pdf_file])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)
