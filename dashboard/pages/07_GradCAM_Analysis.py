import streamlit as st
import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import numpy as np
import cv2
import os

st.set_page_config(
    page_title="VeriShield — GradCAM Analysis",
    page_icon="🔬",
    layout="wide"
)

st.markdown("""
<style>
    .stApp { background-color: #0a0e1a; }
    .main .block-container { padding-top: 1rem; }
    hr { border-color: #1e3a5f !important; }
    p, label, .stMarkdown { color: #cbd5e1 !important; }
    h1, h2, h3 { color: white !important; }
    div[data-testid="stMetricValue"] { color: white !important; }
    div[data-testid="stMetricLabel"] { color: #94a3b8 !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background:linear-gradient(135deg,#0d1b2e,#1a2744);border-radius:16px;
     padding:24px 32px;margin-bottom:24px;border:1px solid #1e3a5f;">
    <h1 style="margin:0;color:white;">🔬 GradCAM Deepfake Analysis</h1>
    <p style="color:#64748b;margin:4px 0 0 0;">
    Visual explanation of WHERE the AI detected deepfake artifacts — red regions indicate suspicious areas
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background:#0f172a;border:1px solid #1e3a5f;border-radius:8px;padding:12px 16px;margin-bottom:16px;">
    <p style="color:#64748b;margin:0;font-size:13px;">
    💡 <b style="color:#cbd5e1;">What is GradCAM?</b> Gradient-weighted Class Activation Mapping shows 
    WHICH pixels the AI model focused on when making its deepfake decision. Red = high suspicion, 
    Blue = low suspicion. This makes AI decisions explainable — required by GDPR Article 22.
    </p>
</div>
""", unsafe_allow_html=True)

@st.cache_resource
def load_face_model():
    model = models.efficientnet_b0(weights='DEFAULT')
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, 2)
    model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'models', 'verishield_face_model.pth')
    if os.path.exists(model_path):
        checkpoint = torch.load(model_path, map_location='cpu')
        if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
            model.load_state_dict(checkpoint['model_state_dict'])
        else:
            model.load_state_dict(checkpoint)
    model.eval()
    return model

def generate_gradcam(model, image_tensor, target_class=None):
    gradients = []
    activations = []

    def backward_hook(module, grad_input, grad_output):
        gradients.append(grad_output[0])

    def forward_hook(module, input, output):
        activations.append(output)

    target_layer = model.features[-1]
    forward_handle = target_layer.register_forward_hook(forward_hook)
    backward_handle = target_layer.register_full_backward_hook(backward_hook)

    output = model(image_tensor)

    if target_class is None:
        target_class = output.argmax(dim=1).item()

    model.zero_grad()
    output[0, target_class].backward()

    forward_handle.remove()
    backward_handle.remove()

    gradient = gradients[0].cpu().detach()
    activation = activations[0].cpu().detach()

    weights = gradient.mean(dim=(2, 3), keepdim=True)
    cam = (weights * activation).sum(dim=1, keepdim=True)
    cam = torch.relu(cam)
    cam = cam.squeeze().numpy()

    if cam.max() > 0:
        cam = (cam - cam.min()) / (cam.max() - cam.min())

    return cam, target_class, torch.softmax(output, dim=1)[0].detach().numpy()

def apply_heatmap(original_image, cam, alpha=0.4):
    img_array = np.array(original_image.resize((224, 224)))
    cam_resized = cv2.resize(cam, (224, 224))
    heatmap = cv2.applyColorMap(np.uint8(255 * cam_resized), cv2.COLORMAP_JET)
    heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
    overlay = (alpha * heatmap + (1 - alpha) * img_array).astype(np.uint8)
    return overlay, heatmap

transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

st.markdown("### 🧬 Face Deepfake GradCAM Analysis")
st.markdown("<p style='color:#64748b;'>Upload a face photo to see exactly WHERE the AI detected deepfake artifacts</p>", unsafe_allow_html=True)

face_file = st.file_uploader("Upload Face Photo", type=['jpg', 'jpeg', 'png'], key="gradcam_face")

if face_file:
    image = Image.open(face_file).convert("RGB")

    if st.button("🔬 Analyze with GradCAM", type="primary", use_container_width=True):
        with st.spinner("Generating GradCAM visualization..."):
            try:
                model = load_face_model()
                tensor = transform(image).unsqueeze(0)
                tensor.requires_grad = True

                cam, pred_class, probs = generate_gradcam(model, tensor)
                overlay, heatmap = apply_heatmap(image, cam)

                fake_prob = float(probs[0])
                real_prob = float(probs[1])

                color = '#dc2626' if fake_prob > 0.5 else '#059669'
                result_text = '🤖 DEEPFAKE DETECTED' if fake_prob > 0.5 else '✅ AUTHENTIC FACE'

                st.markdown(f"""
                <div style="background:#0f172a;border:2px solid {color};border-radius:12px;
                            padding:16px;text-align:center;margin-bottom:16px;">
                    <p style="color:{color};font-size:22px;font-weight:bold;margin:0;">{result_text}</p>
                    <p style="color:#64748b;margin:4px 0 0 0;">
                        Deepfake Probability: {fake_prob:.2%} | Authentic: {real_prob:.2%}
                    </p>
                </div>
                """, unsafe_allow_html=True)

                c1, c2, c3 = st.columns(3)

                with c1:
                    st.markdown("**Original Image**")
                    st.image(image.resize((224, 224)), use_container_width=True)

                with c2:
                    st.markdown("**GradCAM Heatmap**")
                    st.image(heatmap, use_container_width=True)
                    st.caption("🔴 Red = High suspicion | 🔵 Blue = Low suspicion")

                with c3:
                    st.markdown("**Overlay**")
                    st.image(overlay, use_container_width=True)
                    st.caption("Shows WHERE AI detected deepfake artifacts")

                st.divider()
                m1, m2 = st.columns(2)
                with m1: st.metric("Deepfake Probability", f"{fake_prob:.2%}")
                with m2: st.metric("Authentic Probability", f"{real_prob:.2%}")

            except Exception as e:
                st.error(f"GradCAM error: {e}")

st.divider()
st.markdown("""
<div style="background:#0f172a;border:1px solid #1e3a5f;border-radius:8px;padding:16px;">
    <p style="color:#64748b;margin:0;font-size:13px;">
    💡 <b style="color:#cbd5e1;">Why GradCAM matters:</b> GDPR Article 22 requires financial institutions 
    to explain automated decisions. GradCAM makes AI decisions transparent — compliance officers can 
    see exactly WHY a face was flagged as deepfake, not just that it was flagged.
    </p>
</div>
""", unsafe_allow_html=True)