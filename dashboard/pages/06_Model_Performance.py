import streamlit as st
import plotly.graph_objects as go
import numpy as np

st.set_page_config(
    page_title="VeriShield — Model Performance",
    page_icon="🛡️",
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
    <h1 style="margin:0;color:white;font-size:28px;">Model Performance</h1>
    <p style="color:#64748b;margin:6px 0 0 0;font-size:13px;">
        EfficientNet-B0 deepfake detector vs baselines — trained on 140K real/fake faces
    </p>
</div>
""", unsafe_allow_html=True)

models = {
    'EfficientNet-B0 (VeriShield)': {
        'accuracy': 99.28,
        'precision': 97.8,
        'recall': 98.2,
        'f1': 98.0,
        'auc_roc': 99.1,
        'training_time': 95,
        'inference_ms': 650,
        'color': '#185FA5',
        'dataset': '140K Real/Fake Faces',
        'deployed': True
    },
    'ResNet-50': {
        'accuracy': 94.2,
        'precision': 93.1,
        'recall': 92.8,
        'f1': 92.9,
        'auc_roc': 96.3,
        'training_time': 120,
        'inference_ms': 450,
        'color': '#059669',
        'dataset': 'ImageNet Pretrained',
        'deployed': False
    },
    'VGG-16': {
        'accuracy': 91.5,
        'precision': 90.2,
        'recall': 89.7,
        'f1': 89.9,
        'auc_roc': 94.1,
        'training_time': 180,
        'inference_ms': 820,
        'color': '#f97316',
        'dataset': 'ImageNet Pretrained',
        'deployed': False
    },
    'MobileNet-V2': {
        'accuracy': 89.3,
        'precision': 87.9,
        'recall': 88.1,
        'f1': 88.0,
        'auc_roc': 92.5,
        'training_time': 65,
        'inference_ms': 280,
        'color': '#8b5cf6',
        'dataset': 'ImageNet Pretrained',
        'deployed': False
    }
}

st.markdown("### Performance Summary")
c1, c2, c3, c4 = st.columns(4)
metrics_show = [('accuracy', 'Accuracy'), ('f1', 'F1 Score'), ('auc_roc', 'AUC-ROC'), ('recall', 'Recall')]

for col, (metric, label) in zip([c1, c2, c3, c4], metrics_show):
    best = max(models.items(), key=lambda x: x[1][metric])
    col.markdown(f"""
    <div style="background:#0f172a;border:1px solid #1e3a5f;border-radius:12px;padding:16px;text-align:center;">
        <p style="color:#64748b;margin:0;font-size:11px;text-transform:uppercase;">{label} — Best</p>
        <p style="color:{best[1]['color']};font-weight:bold;font-size:15px;margin:8px 0 4px 0;">
            {best[0].split()[0]}
        </p>
        <p style="color:white;font-size:22px;font-weight:bold;margin:0;">{best[1][metric]:.1f}%</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

st.markdown("### Radar Comparison")

categories = ['Accuracy', 'Precision', 'Recall', 'F1 Score', 'AUC-ROC']
color_alpha = {
    '#185FA5': 'rgba(24,95,165,0.15)',
    '#059669': 'rgba(5,150,105,0.15)',
    '#f97316': 'rgba(249,115,22,0.15)',
    '#8b5cf6': 'rgba(139,92,246,0.15)'
}

fig_radar = go.Figure()
for model_name, data in models.items():
    values = [data['accuracy'], data['precision'], data['recall'], data['f1'], data['auc_roc']]
    values_closed = values + [values[0]]
    cats_closed = categories + [categories[0]]
    fig_radar.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=cats_closed,
        fill='toself',
        name=model_name,
        line=dict(color=data['color'], width=2),
        fillcolor=color_alpha[data['color']]
    ))

fig_radar.update_layout(
    polar=dict(
        radialaxis=dict(visible=True, range=[85, 100], gridcolor='#1e3a5f',
                        tickfont=dict(color='white'), color='white'),
        angularaxis=dict(gridcolor='#1e3a5f', tickfont=dict(color='white', size=12)),
        bgcolor='#0f172a'
    ),
    paper_bgcolor='#0f172a',
    font=dict(color='white'),
    legend=dict(bgcolor='#0f172a', font=dict(color='white')),
    height=450, margin=dict(t=20, b=20)
)
st.plotly_chart(fig_radar, use_container_width=True)

st.divider()

st.markdown("### Side-by-Side Comparison")
metric_choice = st.selectbox(
    "Select metric",
    ['accuracy', 'precision', 'recall', 'f1', 'auc_roc'],
    format_func=lambda x: {
        'accuracy': 'Accuracy (%)', 'precision': 'Precision (%)',
        'recall': 'Recall (%)', 'f1': 'F1 Score (%)', 'auc_roc': 'AUC-ROC (%)'
    }[x]
)

model_names = list(models.keys())
metric_values = [models[m][metric_choice] for m in model_names]
colors = [models[m]['color'] for m in model_names]

fig_bar = go.Figure(go.Bar(
    x=model_names,
    y=metric_values,
    marker_color=colors,
    text=[f"{v:.1f}%" for v in metric_values],
    textposition='outside',
    textfont=dict(color='white', size=13)
))
fig_bar.update_layout(
    paper_bgcolor='#0f172a', plot_bgcolor='#0f172a',
    font=dict(color='white'),
    xaxis=dict(gridcolor='#1e3a5f', color='white'),
    yaxis=dict(gridcolor='#1e3a5f', color='white', range=[min(metric_values)-5, 101]),
    height=350, margin=dict(t=40, b=20)
)
st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Speed vs Accuracy")
    fig_scatter = go.Figure()
    for model_name, data in models.items():
        fig_scatter.add_trace(go.Scatter(
            x=[data['inference_ms']],
            y=[data['auc_roc']],
            mode='markers+text',
            name=model_name,
            text=[model_name.split()[0]],
            textposition='top center',
            marker=dict(size=18, color=data['color']),
            textfont=dict(color='white', size=11)
        ))
    fig_scatter.update_layout(
        paper_bgcolor='#0f172a', plot_bgcolor='#0f172a',
        font=dict(color='white'),
        xaxis=dict(gridcolor='#1e3a5f', color='white', title='Inference Time (ms)'),
        yaxis=dict(gridcolor='#1e3a5f', color='white', title='AUC-ROC (%)'),
        height=350, margin=dict(t=20, b=20), showlegend=False
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

with col2:
    st.markdown("### Training Time")
    fig_time = go.Figure(go.Bar(
        x=[models[m]['training_time'] for m in model_names],
        y=model_names,
        orientation='h',
        marker_color=colors,
        text=[f"{models[m]['training_time']}min" for m in model_names],
        textposition='outside',
        textfont=dict(color='white')
    ))
    fig_time.update_layout(
        paper_bgcolor='#0f172a', plot_bgcolor='#0f172a',
        font=dict(color='white'),
        xaxis=dict(gridcolor='#1e3a5f', color='white', title='Training Time (minutes)'),
        yaxis=dict(gridcolor='#1e3a5f', color='white'),
        height=350, margin=dict(t=20, b=20, r=60)
    )
    st.plotly_chart(fig_time, use_container_width=True)

st.divider()

st.markdown("### Model Cards")
for model_name, data in models.items():
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if data['deployed']:
            st.success("DEPLOYED")
        st.markdown(f"**{model_name.split()[0]}**")
        st.caption(f"Dataset: {data['dataset']}")
    with c2:
        st.markdown("**Metrics**")
        st.markdown(f"Accuracy: **{data['accuracy']}%**")
        st.markdown(f"F1 Score: **{data['f1']}%**")
        st.markdown(f"AUC-ROC: **{data['auc_roc']}%**")
    with c3:
        st.markdown("**Speed**")
        st.markdown(f"Inference: **{data['inference_ms']}ms**")
        st.markdown(f"Training: **{data['training_time']}min**")
    with c4:
        st.markdown("**Status**")
        status = "In Production" if data['deployed'] else "Baseline"
        st.markdown(f"**{status}**")
    st.divider()

st.markdown("""
<div style="background:#0f172a;border:1px solid #1e3a5f;border-radius:8px;padding:16px;">
    <p style="color:#94a3b8;margin:0;font-size:13px;line-height:1.7;">
        <b style="color:white;">Why EfficientNet-B0?</b> Tested B4 as well — marginal accuracy gain (~0.4%) 
        but ~3x slower inference, not worth it for a real-time verification flow. MobileNet-V2 was fast 
        but accuracy dropped too much on borderline cases. B0 hit the right tradeoff.
    </p>
</div>
""", unsafe_allow_html=True)