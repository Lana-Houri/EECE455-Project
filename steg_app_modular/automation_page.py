import os
import tempfile
import json
import html
from typing import List, Dict, Any

import streamlit as st
from PIL import Image

from suspicion import analyze_image_suspicion
from statistical_tools import (
    run_stegexpose,
    run_deep_steganalysis,
    calculate_overall_detection_confidence,
)
from decode_tools import (
    run_zsteg,
    run_outguess,
    run_openstego,
    run_steghide,
    run_jsteg,
    run_f5,
)

MIN_SIGNAL_DISPLAY = 1


def _stage_css():
    st.markdown(
        """
        <style>
        .pipeline-stage {
            border-radius: 14px;
            padding: 1rem;
            border: 1px solid rgba(88, 166, 255, 0.3);
            min-height: 120px;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, rgba(20,20,30,0.7), rgba(15,15,25,0.9));
            transition: all 0.3s ease;
            box-shadow: 0 0 20px rgba(0,0,0,0.4);
        }
        .pipeline-stage.pending {
            opacity: 0.6;
        }
        .pipeline-stage.active {
            border-color: #ff007a;
            box-shadow: 0 0 25px rgba(255,0,122,0.5), inset 0 0 10px rgba(255,0,122,0.3);
            background: linear-gradient(135deg, rgba(255,0,122,0.2), rgba(15,15,25,0.8));
        }
        .pipeline-stage.complete {
            border-color: #3fb950;
            box-shadow: 0 0 25px rgba(63,185,80,0.4), inset 0 0 10px rgba(63,185,80,0.25);
            background: linear-gradient(135deg, rgba(63,185,80,0.15), rgba(15,15,25,0.8));
        }
        .stage-title {
            font-size: 1.1rem;
            font-weight: 700;
            margin-bottom: 0.35rem;
        }
        .stage-status {
            font-size: 0.9rem;
            opacity: 0.85;
        }
        .stage-icon {
            font-size: 1.3rem;
            margin-right: 0.4rem;
        }
        .stage-loader {
            position: relative;
            height: 6px;
            border-radius: 999px;
            background: rgba(255,255,255,0.08);
            overflow: hidden;
            margin-top: 0.75rem;
        }
        .stage-loader::after {
            content: "";
            position: absolute;
            left: -35%;
            top: 0;
            width: 35%;
            height: 100%;
            background: linear-gradient(90deg, #ff007a, #58a6ff);
            animation: stageLoaderSlide 1.8s infinite;
            box-shadow: 0 0 8px rgba(88,166,255,0.8);
        }
        @keyframes stageLoaderSlide {
            0% { left: -35%; }
            50% { left: 70%; }
            100% { left: 110%; }
        }
        .tool-chip {
            display: inline-block;
            margin: 0.15rem 0.2rem 0 0;
            padding: 0.2rem 0.6rem;
            border-radius: 999px;
            font-size: 0.75rem;
            background: rgba(88,166,255,0.08);
            border: 1px solid rgba(88,166,255,0.3);
        }
        .tool-chip.done {
            border-color: rgba(63,185,80,0.5);
            background: rgba(63,185,80,0.15);
            color: #3fb950;
        }
        .tool-chip.active {
            border-color: rgba(255,0,122,0.5);
            background: rgba(255,0,122,0.15);
            color: #ff6ac0;
        }
        .suspicion-raw {
            background: #05060d;
            border: 1px solid rgba(88,166,255,0.3);
            border-radius: 10px;
            padding: 1rem;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            color: #e2e8f0;
            overflow-x: auto;
            white-space: pre-wrap;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_stage(placeholder, title: str, status: str, icon: str, message: str, tools: List[Dict[str, str]] = None):
    chips = ""
    if tools:
        for tool in tools:
            chips += f'<span class="tool-chip {tool.get("status", "")}">{tool["label"]}</span>'
    loader = '<div class="stage-loader"></div>' if status == "active" else ""
    placeholder.markdown(
        f"""
        <div class="pipeline-stage {status}">
            <div class="stage-title"><span class="stage-icon">{icon}</span>{title}</div>
            <div class="stage-status">{message}</div>
            <div style="margin-top:0.5rem;">{chips}</div>
            {loader}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _display_decode_results(rows: List[Dict[str, Any]]):
    if not rows:
        st.info("No extraction signals produced by the decode tools.")
        return
    
    strong = [r for r in rows if r.get("Confidence") == "Strong"]
    medium = [r for r in rows if r.get("Confidence") == "Medium"]
    weak = [r for r in rows if r.get("Confidence") == "Weak"]
    
    def _render_group(title, items, css):
        if not items:
            return
        st.markdown(f"""
            <div class="signal-section">
                <div class="signal-header">
                    <div class="signal-title">{title}</div>
                    <div class="signal-count">{len(items)}</div>
                </div>
                <div class="signal-body">
        """, unsafe_allow_html=True)
        for signal in items:
            st.markdown(f"""
                <div class="signal-item {css}">
                    <div class="signal-meta">
                        <span class="signal-tool">{signal.get('Tool')}</span>
                        <span class="signal-layer">{signal.get('Layer','')}</span>
                        <span class="signal-confidence {css.upper()}">{signal.get('Confidence','').upper()}</span>
                    </div>
                    <div class="signal-interpretation">{signal.get('Interpretation','')}</div>
                    <div class="signal-payload-preview">{signal.get('Payload','')}</div>
                </div>
            """, unsafe_allow_html=True)
            payload = (signal.get("Full_Payload") or "").strip()
            if payload and payload.lower() != "no payload":
                with st.expander(f"View Full Payload - {signal.get('Tool','Unknown')}"):
                    st.code(payload, language="text")
        st.markdown("</div></div>", unsafe_allow_html=True)
    
    _render_group("🚨 Strong Signals", strong, "strong")
    _render_group("⚠️ Medium Signals", medium, "medium")
    if weak:
        with st.expander(f"🔍 Weak Signals ({len(weak)}) - click to expand"):
            for signal in weak:
                st.markdown(f"""
                    <div class="signal-item weak">
                        <div class="signal-meta">
                            <span class="signal-tool">{signal.get('Tool')}</span>
                            <span class="signal-layer">{signal.get('Layer','')}</span>
                            <span class="signal-confidence weak">{signal.get('Confidence','').upper()}</span>
                        </div>
                        <div class="signal-interpretation">{signal.get('Interpretation','')}</div>
                        <div class="signal-payload-preview">{signal.get('Payload','')}</div>
                    </div>
                """, unsafe_allow_html=True)
                payload = (signal.get("Full_Payload") or "").strip()
                if payload and payload.lower() != "no payload":
                    with st.expander(f"View Full Payload - {signal.get('Tool','Unknown')}"):
                        st.code(payload, language="text")


def render_automation_page():
    def _notify(message: str, success: bool = True):
        icon = "✅" if success else "⚠️"
        try:
            st.toast(message, icon=icon)
        except Exception:
            st.sidebar.info(f"{icon} {message}")

    _stage_css()
    st.markdown('<h2 class="section-header">🤖 Automated Stego Pipeline</h2>', unsafe_allow_html=True)
    st.markdown("""
        <div class="alert-box alert-info">
            <span class="alert-icon">⚙️</span>
            <div>
                <strong>Black-Box Mode:</strong> Drop an image and let the pipeline orchestrate metadata prep, deep analysis, and decoding.
                Watch each stage light up as tools execute. Only choose whether to include extraction.
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    decode_enabled = st.checkbox("Include decoding / extraction stage", value=True)
    uploaded_file = st.file_uploader(
        "Upload an image to scan automatically",
        type=["png", "jpg", "jpeg"],
        help="Pipeline will run all detectors. Decoding tools run only if enabled.",
    )
    if not uploaded_file:
        return
    
    image = Image.open(uploaded_file)
    width, height = image.size
    file_size = len(uploaded_file.getvalue())
    fmt = image.format or "Unknown"
    is_jpeg = fmt.upper() in ["JPEG", "JPG"]
    
    stage_names = ["Preparation", "Detection", "Decoding" if decode_enabled else "Decoding (skipped)", "Summary"]
    stage_icons = ["📁", "🔬", "🗝️", "📊"]
    cols = st.columns(len(stage_names))
    stage_placeholders = [col.empty() for col in cols]
    
    for idx, name in enumerate(stage_names):
        _render_stage(stage_placeholders[idx], name, "pending", stage_icons[idx], "Waiting...", [])
    
    if not st.button("Start Automated Pipeline", use_container_width=True):
        return
    
    log_placeholder = st.empty()
    logs: List[str] = []
    def log(msg: str):
        logs.append(msg)
        formatted = "<br>".join(f"• {line}" for line in logs[-8:])
        log_placeholder.markdown(f"<div class='card'>{formatted}</div>", unsafe_allow_html=True)
    
    temp_path = os.path.join(tempfile.gettempdir(), uploaded_file.name)
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Stage 1: Prep
    _render_stage(stage_placeholders[0], stage_names[0], "active", stage_icons[0], "Preparing artifact...", [])
    log("Loaded image and captured metadata.")
    prep_tools = [
        {"label": f"{fmt.upper()} format", "status": "done"},
        {"label": f"{width}x{height}px", "status": "done"},
        {"label": f"{file_size/1024:.1f} KB", "status": "done"},
    ]
    _render_stage(stage_placeholders[0], stage_names[0], "complete", stage_icons[0], "Metadata locked in.", prep_tools)
    
    # Stage 2: Detection
    detection_tools = [
        {"label": "Suspicion", "status": ""},
        {"label": "StegExpose", "status": ""},
        {"label": "Deep Scan", "status": ""},
    ]
    _render_stage(stage_placeholders[1], stage_names[1], "active", stage_icons[1], "Running detection suite...", detection_tools)
    progress = st.progress(0)
    progress.progress(5)
    
    suspicion_result = analyze_image_suspicion(temp_path, fmt)
    detection_tools[0]["status"] = "done"
    log("Statistical suspicion analysis completed.")
    progress.progress(35)
    
    stegexpose_result = run_stegexpose(temp_path)
    detection_tools[1]["status"] = "done"
    log("StegExpose finished.")
    progress.progress(65)
    
    deep_result = run_deep_steganalysis(temp_path)
    detection_tools[2]["status"] = "done"
    log("Deep learning / statistical scan finished.")
    progress.progress(90)
    
    detection_results = {
        "suspicion": suspicion_result,
        "stegexpose": stegexpose_result,
        "deep_learning": deep_result,
    }
    detection_summary = calculate_overall_detection_confidence(
        {k: v for k, v in detection_results.items() if k != "suspicion"}
    )
    progress.progress(100)
    _render_stage(stage_placeholders[1], stage_names[1], "complete", stage_icons[1], "Detection suite complete.", detection_tools)
    _notify("Detection analysis finished.", success=True)
    
    # Stage 3: Decoding
    decode_rows: List[Dict[str, Any]] = []
    if decode_enabled:
        decode_tool_labels = ["Zsteg", "Steghide", "OutGuess", "OpenStego", "Jsteg", "F5"]
        decode_status = [{"label": t, "status": ""} for t in decode_tool_labels]
        _render_stage(stage_placeholders[2], stage_names[2], "active", stage_icons[2], "Extracting payloads...", decode_status)
        decode_progress = st.progress(0)
        tool_funcs = [
            run_zsteg,
            lambda path: run_steghide(path, ""),
            run_outguess,
            lambda path: run_openstego(path, ""),
            run_jsteg,
            lambda path: run_f5(path, "abc123"),
        ]
        total = len(tool_funcs)
        for idx, func in enumerate(tool_funcs):
            try:
                _, rows = func(temp_path)
                if rows:
                    decode_rows.extend(rows)
            except Exception as exc:
                log(f"{decode_tool_labels[idx]} error: {exc}")
                _notify(f"{decode_tool_labels[idx]} failed: {exc}", success=False)
            decode_status[idx]["status"] = "done"
            decode_progress.progress(int(((idx + 1) / total) * 100))
            log(f"{decode_tool_labels[idx]} completed.")
            _render_stage(stage_placeholders[2], stage_names[2], "active", stage_icons[2], "Extracting payloads...", decode_status)
        decode_progress.progress(100)
        _render_stage(stage_placeholders[2], stage_names[2], "complete", stage_icons[2], "Decoding suite complete.", decode_status)
        _notify("Decoding tools finished running.", success=True)
    else:
        _render_stage(stage_placeholders[2], stage_names[2], "complete", stage_icons[2], "Decoding skipped by user.", [])
        _notify("Decoding skipped per user setting.", success=False)
    
    # Stage 4: Summary
    _render_stage(stage_placeholders[3], stage_names[3], "active", stage_icons[3], "Compiling reports...", [])
    log("Compiling final summary.")
    
    suspicion_card = suspicion_result
    st.markdown('<h3 class="section-header">📊 Pipeline Summary</h3>', unsafe_allow_html=True)
    
    conf_value = detection_summary["overall_confidence"]
    conf_level = detection_summary["level"]
    conf_color = detection_summary["color"]
    
    st.markdown(f"""
        <div class="confidence-meter">
            <div class="confidence-value">{conf_value:.1f}%</div>
            <div class="confidence-label">{conf_level}</div>
            <div class="progress-container" style="margin-top: 1rem;">
                <div class="progress-bar" style="width: {conf_value}%; transition: width 1s ease;"></div>
            </div>
            <div style="margin-top:0.5rem;font-size:0.9rem;color:var(--text-tertiary);">
                {detection_summary['methods_used']} detection methods executed automatically
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    alert_icon = "🚨" if conf_color == "strong" else "⚠️" if conf_color == "medium" else "✅"
    st.markdown(f"""
        <div class="alert-box alert-{conf_color}">
            <span class="alert-icon">{alert_icon}</span>
            <div><strong>{detection_summary['message']}</strong></div>
        </div>
    """, unsafe_allow_html=True)
    if conf_color == "strong":
        _notify("High likelihood of hidden data detected.", success=False)
    elif conf_color == "medium":
        _notify("Possible steganography indicators found.", success=False)
    else:
        _notify("No strong steganography indicators detected.", success=True)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### 🗂️ Artifact Snapshot")
    st.markdown(f"- **Format:** {fmt}")
    st.markdown(f"- **Dimensions:** {width}x{height}")
    st.markdown(f"- **Size:** {file_size/1024:.1f} KB")
    st.markdown(f"- **JPEG Pipeline:** {'Yes' if is_jpeg else 'No'}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<h3 class="section-header">🔬 Detection Results</h3>', unsafe_allow_html=True)
    detection_cards = []
    detection_cards.append({
        "title": "📉 Suspicion Score",
        "content": lambda: (
            st.metric("Score", f"{suspicion_card['suspicion_score']}"),
            st.markdown(f"**Level:** {suspicion_card['level']}")
        )
    })
    if stegexpose_result.get("success"):
        detection_cards.append({
            "title": "🔍 StegExpose",
            "content": lambda: (
                st.metric("Confidence", f"{stegexpose_result['confidence']:.1f}%"),
                st.markdown(f"**Status:** {'Detected' if stegexpose_result.get('is_stego') else 'Clean'}")
            )
        })
    if deep_result.get("success"):
        detection_cards.append({
            "title": "🧠 Deep Scan",
            "content": lambda: (
                st.metric("Confidence", f"{deep_result['confidence']:.1f}%"),
                st.markdown(f"**Status:** {'Detected' if deep_result.get('is_stego') else 'Clean'}"),
                st.markdown(f"**Method:** {deep_result.get('method_type','N/A')}")
            )
        })
    cols = st.columns(len(detection_cards) or 1)
    for idx, card in enumerate(detection_cards):
        with cols[idx]:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown(f"#### {card['title']}")
            card["content"]()
            st.markdown('</div>', unsafe_allow_html=True)
    
    with st.expander("Detection Details (raw outputs)"):
        st.markdown("##### Suspicion Details")
        suspicion_details = suspicion_card.get("details", {})
        if suspicion_details:
            escaped = html.escape(json.dumps(suspicion_details, indent=2))
            st.markdown(f"<pre class='suspicion-raw'>{escaped}</pre>", unsafe_allow_html=True)
        else:
            st.info("No additional suspicion metadata.")
        if stegexpose_result.get("raw_output"):
            st.markdown("##### StegExpose Output")
            st.code(stegexpose_result["raw_output"], language="text")
        if deep_result.get("raw_output"):
            st.markdown("##### Deep Scan Output")
            st.code(deep_result["raw_output"], language="text")
    
    if decode_enabled and len(decode_rows) >= MIN_SIGNAL_DISPLAY:
        st.markdown('<h3 class="section-header">🧬 Decoding Signals</h3>', unsafe_allow_html=True)
        _display_decode_results(decode_rows)
        _notify("Decoding signals available. Review details.", success=True)
    elif decode_enabled:
        _notify("Decoding finished with no signals found.", success=True)
    
    _render_stage(stage_placeholders[3], stage_names[3], "complete", stage_icons[3], "Reports ready.", [])
    _notify("Automation pipeline complete.", success=True)
