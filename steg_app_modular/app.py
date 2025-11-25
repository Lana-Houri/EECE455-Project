import streamlit as st
import subprocess
import tempfile
import os
import re
import pandas as pd
import math
import numpy as np
from datetime import datetime
from collections import Counter
from PIL import Image

# =====================================
# Page Configuration
# =====================================
st.set_page_config(
    page_title="Universal Steg Analyzer",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Force dark theme
st.markdown("""
    <style>
    /* Override Streamlit's default theme */
    .stApp {
        background-color: #0d1117 !important;
    }
    </style>
""", unsafe_allow_html=True)

# =====================================
# Clean Dark Theme
# =====================================
st.markdown(
    """
    <style>
    
      @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap');
      
      * {
        font-family: 'Inter', sans-serif;
        box-sizing: border-box;
      }
      
      code, pre {
        font-family: 'JetBrains Mono', monospace;
      }
      
      /* Color Variables - High Contrast */
      :root {
        --bg-primary: #0d1117;
        --bg-secondary: #161b22;
        --bg-card: #1c2128;
        --bg-hover: #21262d;
        --text-primary: #ffffff;
        --text-secondary: #e6edf3;
        --text-tertiary: #8b949e;
        --accent-primary: #58a6ff;
        --accent-success: #3fb950;
        --accent-warning: #d29922;
        --accent-error: #f85149;
        --accent-info: #58a6ff;
        --border-color: #30363d;
        --border-accent: #21262d;
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.5);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.6);
      }
      
      /* Hide Streamlit Branding */
      #MainMenu {visibility: hidden;}
      footer {visibility: hidden;}
      header {visibility: hidden;}
      
      /* Force Dark Theme - Override Streamlit Defaults */
      .stApp {
        background-color: var(--bg-primary) !important;
        color: var(--text-primary) !important;
      }
      
      .main .block-container {
        background-color: var(--bg-primary) !important;
        color: var(--text-primary) !important;
      }
      
      /* Override all white backgrounds */
      div[data-baseweb] {
        background-color: var(--bg-primary) !important;
        color: var(--text-primary) !important;
      }
      
      /* Force dark backgrounds on all elements */
      section[data-testid="stSidebar"],
      section[data-testid="stSidebar"] > div,
      section[data-testid="stSidebar"] > div > div {
        background-color: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
      }
      
      /* Main content area */
      section.main .block-container {
        background-color: var(--bg-primary) !important;
      }
      
      /* All text elements */
      p, span, div, label, h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary) !important;
      }
      
      /* Streamlit markdown containers */
      .stMarkdown {
        color: var(--text-secondary) !important;
      }
      
      .stMarkdown p, .stMarkdown div, .stMarkdown span {
        color: var(--text-secondary) !important;
      }
      
      .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, 
      .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
        color: var(--text-primary) !important;
      }
      
      /* Input labels */
      label, .stTextInput label, .stTextArea label,
      .stSelectbox label, .stMultiSelect label {
        color: var(--text-primary) !important;
      }
      
      /* Scrollbar */
      ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
      }
      
      ::-webkit-scrollbar-track {
        background: var(--bg-secondary);
      }
      
      ::-webkit-scrollbar-thumb {
        background: var(--border-accent);
        border-radius: 5px;
      }
      
      ::-webkit-scrollbar-thumb:hover {
        background: var(--border-color);
      }
      
      /* Main container */
      .main {
        background: var(--bg-primary);
        color: var(--text-primary);
      }
      
      .block-container {
        padding: 1.5rem 2rem;
        max-width: 1400px;
        color: var(--text-primary);
      }
      
      /* Body and root elements */
      body {
        background-color: var(--bg-primary) !important;
        color: var(--text-primary) !important;
      }
      
      html {
        background-color: var(--bg-primary) !important;
      }
      
      /* Sidebar */
      [data-testid="stSidebar"] {
        background: var(--bg-secondary);
        border-right: 1px solid var(--border-color);
      }
      
      [data-testid="stSidebar"] > div:first-child {
        padding: 0;
      }
      
      /* Header with Animated Gradient */
      .app-header {
        background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-secondary) 50%, var(--bg-card) 100%);
        background-size: 200% 200%;
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem 2rem;
        margin-bottom: 1.5rem;
        box-shadow: var(--shadow-md);
        position: relative;
        overflow: hidden;
        animation: gradientShift 8s ease infinite;
      }
      
      .app-header::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(
          135deg,
          rgba(88, 166, 255, 0.1) 0%,
          rgba(88, 166, 255, 0.05) 25%,
          rgba(88, 166, 255, 0.1) 50%,
          rgba(88, 166, 255, 0.05) 75%,
          rgba(88, 166, 255, 0.1) 100%
        );
        background-size: 300% 300%;
        animation: gradientFlow 10s ease infinite;
        z-index: 0;
      }
      
      .app-header::after {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(
          circle,
          rgba(88, 166, 255, 0.15) 0%,
          transparent 70%
        );
        animation: rotateGlow 15s linear infinite;
        z-index: 0;
      }
      
      @keyframes gradientShift {
        0% {
          background-position: 0% 50%;
        }
        50% {
          background-position: 100% 50%;
        }
        100% {
          background-position: 0% 50%;
        }
      }
      
      @keyframes gradientFlow {
        0% {
          background-position: 0% 50%;
        }
        50% {
          background-position: 100% 50%;
        }
        100% {
          background-position: 0% 50%;
        }
      }
      
      @keyframes rotateGlow {
        0% {
          transform: rotate(0deg);
        }
        100% {
          transform: rotate(360deg);
        }
      }
      
      .header-content {
        position: relative;
        z-index: 1;
      }
      
      .header-title {
        font-size: 2rem;
        font-weight: 700;
        color: var(--text-primary);
        margin: 0;
        text-shadow: 0 2px 8px rgba(88, 166, 255, 0.3), 0 0 20px rgba(88, 166, 255, 0.2);
        position: relative;
        z-index: 1;
      }
      
      .header-subtitle {
        font-size: 1rem;
        color: var(--text-secondary);
        margin: 0.5rem 0 0 0;
        font-weight: 400;
        position: relative;
        z-index: 1;
      }
      
      /* Cards - Force dark */
      .card {
        background-color: var(--bg-card) !important;
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 1.25rem;
        box-shadow: var(--shadow-md);
        margin-bottom: 1rem;
        color: var(--text-primary) !important;
      }
      
      .card p, .card div, .card span, .card h1, .card h2, .card h3, .card h4 {
        color: inherit;
      }
      
      /* Section Headers */
      .section-header {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--text-primary);
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid var(--accent-primary);
      }
      
      /* Headings */
      h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary) !important;
      }
      
      /* Paragraphs and general text */
      p {
        color: var(--text-secondary) !important;
      }
      
      /* Divs and spans inherit from parent */
      div, span {
        color: inherit;
      }
      
      /* Signal Results */
      .signal-section {
        margin: 1.5rem 0;
      }
      
      .signal-header {
        background: var(--bg-secondary);
        padding: 0.875rem 1.25rem;
        border-radius: 8px 8px 0 0;
        border: 1px solid var(--border-accent);
        border-bottom: none;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      
      .signal-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--text-primary);
      }
      
      .signal-count {
        background: var(--accent-primary);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
      }
      
      .signal-body {
        background: var(--bg-card);
        padding: 1.25rem;
        border-radius: 0 0 8px 8px;
        border: 1px solid var(--border-accent);
        border-top: none;
      }
      
      .signal-item {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-left: 4px solid;
        border-radius: 6px;
        padding: 1rem;
        margin-bottom: 0.75rem;
      }
      
      .signal-item.strong {
        border-left-color: var(--accent-error);
        background: rgba(248, 113, 113, 0.08);
      }
      
      .signal-item.medium {
        border-left-color: var(--accent-warning);
        background: rgba(251, 191, 36, 0.08);
      }
      
      .signal-item.weak {
        border-left-color: var(--accent-success);
        background: rgba(52, 211, 153, 0.08);
      }
      
      .signal-meta {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 0.5rem;
        flex-wrap: wrap;
      }
      
      .signal-tool {
        font-weight: 600;
        font-size: 1rem;
        color: var(--accent-primary);
      }
      
      .signal-layer {
        font-size: 0.85rem;
        color: var(--text-tertiary);
        font-family: 'JetBrains Mono', monospace;
      }
      
      .signal-confidence {
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
      }
      
      .signal-confidence.strong {
        background: rgba(248, 113, 113, 0.2);
        color: var(--accent-error);
        border: 1px solid var(--accent-error);
      }
      
      .signal-confidence.medium {
        background: rgba(251, 191, 36, 0.2);
        color: var(--accent-warning);
        border: 1px solid var(--accent-warning);
      }
      
      .signal-confidence.weak {
        background: rgba(52, 211, 153, 0.2);
        color: var(--accent-success);
        border: 1px solid var(--accent-success);
      }
      
      .signal-interpretation {
        color: var(--text-secondary);
        margin: 0.5rem 0;
        font-size: 0.9rem;
        line-height: 1.6;
        font-weight: 400;
      }
      
      .signal-payload-preview {
        background: var(--bg-primary);
        border: 1px solid var(--border-color);
        border-radius: 4px;
        padding: 0.625rem;
        margin-top: 0.625rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        color: var(--text-secondary);
        max-height: 80px;
        overflow: hidden;
      }
      
      /* Metrics Grid */
      .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 0.75rem;
        margin: 1rem 0;
      }
      
      .metric-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
        min-height: 100px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        word-wrap: break-word;
        overflow-wrap: break-word;
      }
      
      .metric-label {
        font-size: 0.8rem;
        color: var(--text-secondary);
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.5rem;
        word-wrap: break-word;
        overflow-wrap: break-word;
      }
      
      .metric-value {
        font-size: 1.75rem;
        font-weight: 700;
        color: var(--accent-primary);
        text-shadow: 0 0 10px rgba(88, 166, 255, 0.3);
        word-wrap: break-word;
        overflow-wrap: break-word;
        line-height: 1.2;
      }
      
      /* Dynamic font sizing for metric values */
      .metric-value.dynamic {
        font-size: clamp(1rem, 2.5vw, 1.75rem);
      }
      
      /* Alert Boxes */
      .alert-box {
        border-radius: 8px;
        padding: 1rem 1.25rem;
        margin: 1rem 0;
        border-left: 4px solid;
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        font-size: 0.95rem;
        line-height: 1.5;
      }
      
      .alert-strong {
        background: rgba(248, 113, 113, 0.1);
        border-left-color: var(--accent-error);
        color: var(--accent-error);
      }
      
      .alert-medium {
        background: rgba(251, 191, 36, 0.15);
        border-left-color: var(--accent-warning);
        color: #ffd700;
      }
      
      .alert-weak {
        background: rgba(52, 211, 153, 0.1);
        border-left-color: var(--accent-success);
        color: var(--accent-success);
      }
      
      .alert-info {
        background: rgba(56, 189, 248, 0.1);
        border-left-color: var(--accent-info);
        color: var(--accent-info);
      }
      
      .alert-icon {
        font-size: 1.25rem;
        min-width: 1.25rem;
        font-weight: bold;
        flex-shrink: 0;
      }
      
      /* Progress Bar */
      .progress-container {
        background: var(--bg-secondary);
        border-radius: 8px;
        height: 12px;
        overflow: hidden;
        margin: 1rem 0;
        border: 1px solid var(--border-color);
      }
      
      .progress-bar {
        height: 100%;
        background: var(--accent-primary);
        border-radius: 8px;
        transition: width 0.5s ease;
      }
      
      /* Sidebar */
      [data-testid="stSidebar"] {
        color: var(--text-primary) !important;
      }
      
      [data-testid="stSidebar"] h1,
      [data-testid="stSidebar"] h2,
      [data-testid="stSidebar"] h3,
      [data-testid="stSidebar"] h4 {
        color: var(--text-primary) !important;
      }
      
      .sidebar-logo {
        text-align: center;
        padding: 1.5rem 1rem;
        border-bottom: 2px solid var(--border-color);
        margin-bottom: 1rem;
      }
      
      .sidebar-logo-icon {
        width: 50px;
        height: 50px;
        background: var(--bg-card);
        border: 2px solid var(--accent-primary);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto 0.75rem;
        font-size: 1.75rem;
      }
      
      .sidebar-logo-text {
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--accent-primary);
      }
      
      /* Navigation Buttons */
      .stButton > button {
        width: 100%;
        background: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border: 2px solid var(--border-color) !important;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        font-weight: 600;
        font-size: 0.95rem;
        transition: all 0.2s ease;
        text-align: left;
        margin: 0.3rem 0;
      }
      
      .stButton > button:hover {
        background: var(--bg-hover) !important;
        border-color: var(--accent-primary) !important;
        color: var(--accent-primary) !important;
        transform: translateX(3px);
      }
      
      /* File Uploader - Neon Red Highlight */
      [data-testid="stFileUploader"] {
        background: var(--bg-card);
        border: 3px dashed var(--border-color);
        border-radius: 12px;
        padding: 2rem;
        position: relative;
        transition: all 0.3s ease;
        overflow: hidden;
      }
      
      [data-testid="stFileUploader"]::before {
        content: '';
        position: absolute;
        top: -2px;
        left: -2px;
        right: -2px;
        bottom: -2px;
        background: linear-gradient(45deg, #ff006e, #ff006e, #ff1744, #ff006e);
        background-size: 200% 200%;
        border-radius: 12px;
        z-index: -1;
        opacity: 0;
        animation: neonPulse 2s ease-in-out infinite;
        transition: opacity 0.3s ease;
      }
      
      [data-testid="stFileUploader"]:hover::before {
        opacity: 1;
      }
      
      [data-testid="stFileUploader"]::after {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 0, 110, 0.3), transparent);
        transition: left 0.5s ease;
      }
      
      [data-testid="stFileUploader"]:hover::after {
        left: 100%;
      }
      
      [data-testid="stFileUploader"]:hover {
        border-color: #ff006e;
        box-shadow: 0 0 20px rgba(255, 0, 110, 0.5),
                    0 0 40px rgba(255, 0, 110, 0.3),
                    0 0 60px rgba(255, 0, 110, 0.2);
        transform: translateY(-2px);
      }
      
      @keyframes neonPulse {
        0%, 100% {
          background-position: 0% 50%;
          opacity: 0.6;
        }
        50% {
          background-position: 100% 50%;
          opacity: 1;
        }
      }
      
      /* Expander - Force dark with high contrast text */
      .streamlit-expanderHeader {
        background-color: var(--bg-card) !important;
        background: var(--bg-card) !important;
        border: 1px solid var(--border-color);
        border-radius: 8px;
        font-weight: 600;
        color: var(--text-primary) !important;
      }
      
      .streamlit-expanderHeader:hover {
        background-color: var(--bg-hover) !important;
        background: var(--bg-hover) !important;
        border-color: var(--accent-primary) !important;
      }
      
      .streamlit-expanderContent {
        background-color: var(--bg-primary) !important;
        background: var(--bg-primary) !important;
        color: var(--text-primary) !important;
        padding: 1rem !important;
        border: 1px solid var(--border-color) !important;
        border-top: none !important;
        border-radius: 0 0 8px 8px !important;
      }
      
      .streamlit-expanderContent p,
      .streamlit-expanderContent div,
      .streamlit-expanderContent span,
      .streamlit-expanderContent li,
      .streamlit-expanderContent ul,
      .streamlit-expanderContent ol {
        color: var(--text-primary) !important;
        background-color: transparent !important;
      }
      
      .streamlit-expanderContent h1,
      .streamlit-expanderContent h2,
      .streamlit-expanderContent h3,
      .streamlit-expanderContent h4,
      .streamlit-expanderContent h5,
      .streamlit-expanderContent h6 {
        color: var(--text-primary) !important;
        background-color: transparent !important;
      }
      
      .streamlit-expanderContent strong,
      .streamlit-expanderContent b {
        color: var(--text-primary) !important;
        font-weight: 700 !important;
      }
      
      .streamlit-expanderContent code {
        background-color: var(--bg-secondary) !important;
        background: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        padding: 0.25rem 0.5rem !important;
      }
      
      .streamlit-expanderContent pre {
        background-color: var(--bg-secondary) !important;
        background: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        padding: 1rem !important;
      }
      
      .streamlit-expanderContent pre code {
        background-color: transparent !important;
        border: none !important;
        padding: 0 !important;
      }
      
      /* JSON viewer in expanders */
      .streamlit-expanderContent [data-testid="stJson"] {
        background-color: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
      }
      
      /* Tables in expanders */
      .streamlit-expanderContent table {
        background-color: var(--bg-card) !important;
        color: var(--text-primary) !important;
      }
      
      .streamlit-expanderContent table td,
      .streamlit-expanderContent table th {
        background-color: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border-color: var(--border-color) !important;
      }
      
      /* Markdown in expanders */
      .streamlit-expanderContent .stMarkdown {
        color: var(--text-primary) !important;
      }
      
      .streamlit-expanderContent .stMarkdown p,
      .streamlit-expanderContent .stMarkdown div,
      .streamlit-expanderContent .stMarkdown span {
        color: var(--text-primary) !important;
      }
      
      .streamlit-expanderContent .stMarkdown h1,
      .streamlit-expanderContent .stMarkdown h2,
      .streamlit-expanderContent .stMarkdown h3,
      .streamlit-expanderContent .stMarkdown h4 {
        color: var(--text-primary) !important;
      }
      
      /* Lists in expanders */
      .streamlit-expanderContent ul,
      .streamlit-expanderContent ol {
        color: var(--text-primary) !important;
      }
      
      .streamlit-expanderContent li {
        color: var(--text-primary) !important;
      }
      
      /* Ensure all text elements in expanders are visible */
      .streamlit-expanderContent * {
        color: inherit !important;
      }
      
      .streamlit-expanderContent {
        background-color: var(--bg-primary) !important;
      }
      
      /* Tooltip styling - black text on white background */
      [data-testid="stTooltip"] {
        color: #000000 !important;
      }
      
      [data-testid="stTooltip"] * {
        color: #000000 !important;
      }
      
      /* Baseweb tooltip (used by Streamlit) */
      [data-baseweb="tooltip"] {
        color: #000000 !important;
        background-color: #ffffff !important;
      }
      
      [data-baseweb="tooltip"] * {
        color: #000000 !important;
      }
      
      /* Streamlit help tooltip */
      .stTooltip {
        color: #000000 !important;
        background-color: #ffffff !important;
      }
      
      .stTooltip * {
        color: #000000 !important;
      }
      
      /* Data Tables */
      .stDataFrame {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid var(--border-color);
      }
      
      /* Text Input - Force dark styling */
      .stTextInput > div > div > input,
      .stTextArea > div > div > textarea {
        background-color: var(--bg-secondary) !important;
        background: var(--bg-secondary) !important;
        border: 2px solid var(--border-color) !important;
        border-radius: 6px;
        color: var(--text-primary) !important;
        padding: 0.75rem;
      }
      
      .stTextInput > div > div > input:focus,
      .stTextArea > div > div > textarea:focus {
        border-color: var(--accent-primary) !important;
        outline: 2px solid var(--accent-primary) !important;
        outline-offset: 2px;
        background-color: var(--bg-card) !important;
        background: var(--bg-card) !important;
        color: var(--text-primary) !important;
      }
      
      /* Input wrapper backgrounds */
      .stTextInput > div,
      .stTextArea > div {
        background-color: transparent !important;
      }
      
      .stTextInput > div > div,
      .stTextArea > div > div {
        background-color: transparent !important;
      }
      
      /* Select Box - Force dark */
      .stSelectbox > div > div,
      .stMultiSelect > div > div {
        background-color: var(--bg-secondary) !important;
        background: var(--bg-secondary) !important;
        border: 2px solid var(--border-color) !important;
        border-radius: 6px;
        color: var(--text-primary) !important;
      }
      
      .stSelectbox > div > div > div,
      .stMultiSelect > div > div > div {
        background-color: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
      }
      
      .stSelectbox label,
      .stMultiSelect label {
        color: var(--text-primary) !important;
        font-weight: 500;
      }
      
      /* Select dropdown */
      [data-baseweb="select"] {
        background-color: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
      }
      
      [data-baseweb="popover"] {
        background-color: var(--bg-card) !important;
        color: var(--text-primary) !important;
      }
      
      /* Checkbox */
      .stCheckbox label {
        color: var(--text-primary) !important;
        font-size: 0.95rem;
        font-weight: 400;
      }
      
      /* File Uploader - Force dark with Neon Red */
      [data-testid="stFileUploader"] {
        background-color: var(--bg-secondary) !important;
        background: var(--bg-secondary) !important;
      }
      
      [data-testid="stFileUploader"] > div {
        background-color: var(--bg-secondary) !important;
        background: var(--bg-secondary) !important;
        border: 3px dashed var(--border-color) !important;
        color: var(--text-primary) !important;
        border-radius: 12px !important;
        padding: 2rem !important;
        position: relative !important;
        transition: all 0.3s ease !important;
        overflow: hidden !important;
      }
      
      [data-testid="stFileUploader"] > div::before {
        content: '';
        position: absolute;
        top: -2px;
        left: -2px;
        right: -2px;
        bottom: -2px;
        background: linear-gradient(45deg, #ff006e, #ff1744, #ff006e, #ff1744);
        background-size: 300% 300%;
        border-radius: 12px;
        z-index: -1;
        opacity: 0;
        animation: neonGlow 3s ease-in-out infinite;
        transition: opacity 0.3s ease;
      }
      
      [data-testid="stFileUploader"] > div:hover::before {
        opacity: 1;
      }
      
      [data-testid="stFileUploader"] > div:hover {
        border-color: #ff006e !important;
        background-color: rgba(255, 0, 110, 0.05) !important;
        background: rgba(255, 0, 110, 0.05) !important;
        box-shadow: 0 0 25px rgba(255, 0, 110, 0.6),
                    0 0 50px rgba(255, 0, 110, 0.4),
                    0 0 75px rgba(255, 0, 110, 0.2),
                    inset 0 0 20px rgba(255, 0, 110, 0.1) !important;
        transform: translateY(-3px) scale(1.01) !important;
      }
      
      [data-testid="stFileUploader"] p,
      [data-testid="stFileUploader"] span,
      [data-testid="stFileUploader"] div {
        color: #ffffff !important;
        position: relative;
        z-index: 1;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.8), 0 0 10px rgba(0, 0, 0, 0.5) !important;
      }
      
      [data-testid="stFileUploader"] p:hover,
      [data-testid="stFileUploader"] span:hover {
        color: #ff006e !important;
        text-shadow: 0 0 15px rgba(255, 0, 110, 0.8), 
                     0 0 25px rgba(255, 0, 110, 0.5),
                     0 2px 4px rgba(0, 0, 0, 0.8) !important;
      }
      
      /* File Uploader Text Styling - High Contrast */
      [data-testid="stFileUploader"] p {
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        color: #ffffff !important;
        text-shadow: 0 2px 6px rgba(0, 0, 0, 0.9), 
                     0 0 15px rgba(255, 0, 110, 0.3),
                     2px 2px 4px rgba(0, 0, 0, 0.8) !important;
        letter-spacing: 0.5px !important;
      }
      
      [data-testid="stFileUploader"] span {
        color: #ffffff !important;
        font-weight: 600 !important;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.8) !important;
      }
      
      [data-testid="stFileUploader"] strong {
        color: #ff006e !important;
        text-shadow: 0 0 12px rgba(255, 0, 110, 0.7), 
                     0 0 20px rgba(255, 0, 110, 0.5),
                     0 2px 4px rgba(0, 0, 0, 0.8) !important;
        font-weight: 800 !important;
        font-size: 1.15rem !important;
        letter-spacing: 0.5px !important;
      }
      
      /* Small text in uploader */
      [data-testid="stFileUploader"] small {
        color: #e6edf3 !important;
        font-weight: 600 !important;
        text-shadow: 0 1px 3px rgba(0, 0, 0, 0.8) !important;
      }
      
      /* Drag over state */
      [data-testid="stFileUploader"]:has(input:focus),
      [data-testid="stFileUploader"]:has(input:hover) {
        border-color: #ff006e !important;
      }
      
      @keyframes neonGlow {
        0%, 100% {
          background-position: 0% 50%;
          filter: brightness(1);
        }
        50% {
          background-position: 100% 50%;
          filter: brightness(1.3);
        }
      }
      
      /* Upload icon styling */
      [data-testid="stFileUploader"] svg {
        filter: drop-shadow(0 0 5px rgba(255, 0, 110, 0.5));
      }
      
      [data-testid="stFileUploader"]:hover svg {
        filter: drop-shadow(0 0 10px rgba(255, 0, 110, 0.8));
        animation: iconPulse 1.5s ease-in-out infinite;
      }
      
      @keyframes iconPulse {
        0%, 100% {
          transform: scale(1);
          opacity: 1;
        }
        50% {
          transform: scale(1.1);
          opacity: 0.8;
        }
      }
      
      /* Buttons - Force dark */
      .stButton > button {
        background-color: var(--bg-card) !important;
        background: var(--bg-card) !important;
        color: var(--text-primary) !important;
        border: 2px solid var(--border-color) !important;
      }
      
      .stButton > button:hover {
        background-color: var(--bg-hover) !important;
        background: var(--bg-hover) !important;
        border-color: var(--accent-primary) !important;
        color: var(--accent-primary) !important;
      }
      
      .stButton > button:focus {
        background-color: var(--bg-hover) !important;
        background: var(--bg-hover) !important;
        color: var(--text-primary) !important;
      }
      
      /* Metrics */
      [data-testid="stMetricValue"] {
        color: var(--accent-primary) !important;
      }
      
      [data-testid="stMetricLabel"] {
        color: var(--text-secondary) !important;
      }
      
      /* Expander - Additional styling */
      .streamlit-expanderHeader {
        color: var(--text-primary) !important;
        background-color: var(--bg-card) !important;
      }
      
      .streamlit-expanderContent {
        background-color: var(--bg-primary) !important;
        color: var(--text-primary) !important;
      }
      
      .streamlit-expanderContent * {
        color: var(--text-primary) !important;
      }
      
      /* Code blocks - Force dark */
      code {
        background-color: var(--bg-primary) !important;
        background: var(--bg-primary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
      }
      
      pre {
        background-color: var(--bg-primary) !important;
        background: var(--bg-primary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
      }
      
      .stCodeBlock {
        background-color: var(--bg-secondary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 6px !important;
      }
      
      .stCodeBlock pre {
        background-color: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
        padding: 1rem !important;
      }
      
      .stCodeBlock code {
        background-color: transparent !important;
        color: var(--text-primary) !important;
      }
      
      /* JSON viewer */
      [data-testid="stJson"] {
        background-color: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 6px !important;
        padding: 1rem !important;
      }
      
      [data-testid="stJson"] * {
        color: var(--text-primary) !important;
      }
      
      /* Footer */
      .custom-footer {
        text-align: center;
        padding: 1.5rem 0;
        margin-top: 2rem;
        border-top: 1px solid var(--border-color);
        color: var(--text-tertiary);
        font-size: 0.85rem;
      }
      
      /* Status indicator */
      .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 0.5rem;
        background: var(--accent-success);
      }
      
      /* Confidence meter */
      .confidence-meter {
        text-align: center;
        padding: 2rem;
        background: var(--bg-card);
        border: 1px solid var(--border-accent);
        border-radius: 12px;
        margin: 1.5rem 0;
      }
      
      .confidence-value {
        font-size: 3.5rem;
        font-weight: 800;
        color: var(--accent-primary);
        text-shadow: 0 0 15px rgba(88, 166, 255, 0.4);
      }
      
      .confidence-label {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-top: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 1px;
      }
      
      /* Chatbot */
      .chatbot-container {
        margin-top: 1rem;
      }
      
      .chat-message {
        margin-bottom: 0.75rem;
      }
      
      .chat-message.user {
        text-align: right;
      }
      
      .chat-bubble {
        display: inline-block;
        padding: 0.625rem 0.875rem;
        border-radius: 8px;
        max-width: 80%;
        word-wrap: break-word;
        font-size: 0.9rem;
      }
      
      .chat-bubble.user {
        background: var(--accent-primary);
        color: #ffffff;
        font-weight: 500;
      }
      
      .chat-bubble.assistant {
        background: var(--bg-secondary);
        color: var(--text-primary);
        border: 1px solid var(--border-color);
        font-weight: 400;
      }
      
      /* Method cards grid */
      .method-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
      }
      
      .method-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 1.25rem;
        text-align: center;
      }
      
      .method-card.detected {
        border-color: var(--accent-error);
        background: rgba(248, 113, 113, 0.05);
      }
      
      .method-card.clean {
        border-color: var(--accent-success);
        background: rgba(52, 211, 153, 0.05);
      }
    </style>
    """,
    unsafe_allow_html=True,
)

# =====================================
# Imports from modules
# =====================================
from statistical_tools import (
    run_stegexpose, 
    run_deep_steganalysis, 
    run_rs_analysis,
    run_spa_analysis,
    run_aletheia_detection,
    calculate_overall_detection_confidence
)
from suspicion import analyze_image_suspicion
from external_tools import run_exiftool, run_binwalk, check_trailer_manual
from parsers import (is_printable_text, calculate_entropy, is_error_or_status_message, classify_result, parse_tool_output)
from decode_tools import (run_zsteg, run_outguess, run_openstego, run_steghide, run_jsteg, run_f5)
from encode_tools import encode_openstego, encode_steghide

# =====================================
# Session State Management
# =====================================
if 'current_page' not in st.session_state:
    st.session_state.current_page = 'Analyze'
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []
if 'gemini_api_key' not in st.session_state:
    st.session_state.gemini_api_key = ""

# =====================================
# Gemini Chatbot Helper Function
# =====================================
def send_to_gemini(message: str, api_key: str):
    """Send message to Gemini API for cryptography help."""
    if not api_key:
        return "Please set your Gemini API key in the sidebar first."
    
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        system_prompt = """You are a helpful assistant specializing in steganography and cryptography concepts. 
        You help users understand:
        - Steganography techniques (LSB, DCT, spread spectrum, etc.)
        - Cryptographic algorithms used in this tool
        - How different detection methods work
        - Interpreting analysis results
        
        Keep responses concise, technical, and educational. Focus on explaining concepts related to the Universal Steg Analyzer tool."""
        
        full_prompt = f"{system_prompt}\n\nUser question: {message}"
        
        response = model.generate_content(full_prompt)
        return response.text
    except ImportError:
        return "Gemini library not installed. Run: pip install google-generativeai --break-system-packages"
    except Exception as e:
        return f"Error connecting to Gemini: {str(e)}"

# =====================================
# Sidebar Navigation
# =====================================
with st.sidebar:
    st.markdown("""
        <div class="sidebar-logo">
            <div class="sidebar-logo-icon">&#x1F512;</div>
            <div class="sidebar-logo-text">StegAnalyzer</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### Navigation")
    
    if st.button("🔬 Analyze", key="nav_Analyze", use_container_width=True):
        st.session_state.current_page = 'Analyze'
        st.rerun()
    
    if st.button("🔓 Decode", key="nav_Decode", use_container_width=True):
        st.session_state.current_page = 'Decode'
        st.rerun()
    
    if st.button("🔒 Encode", key="nav_Encode", use_container_width=True):
        st.session_state.current_page = 'Encode'
        st.rerun()
    
    if st.button("ℹ️ About", key="nav_About", use_container_width=True):
        st.session_state.current_page = 'About'
        st.rerun()
    
    st.markdown("---")
    st.markdown("### Gemini API Key")
    api_key_input = st.text_input("Enter API Key", type="password", value=st.session_state.gemini_api_key, key="api_key_input")
    if api_key_input != st.session_state.gemini_api_key:
        st.session_state.gemini_api_key = api_key_input
    
    st.markdown("---")
    st.markdown("### 🛠️ Detection Methods")
    st.markdown("**Extraction Tools:**")
    st.markdown('<span class="status-dot"></span> Zsteg (PNG)', unsafe_allow_html=True)
    st.markdown('<span class="status-dot"></span> Steghide (JPEG)', unsafe_allow_html=True)
    st.markdown('<span class="status-dot"></span> OutGuess', unsafe_allow_html=True)
    st.markdown('<span class="status-dot"></span> OpenStego', unsafe_allow_html=True)
    
    st.markdown("**Statistical Analysis:**")
    st.markdown('<span class="status-dot"></span> StegExpose', unsafe_allow_html=True)
    st.markdown('<span class="status-dot"></span> Chi-Square', unsafe_allow_html=True)
    st.markdown('<span class="status-dot"></span> DCT Analysis', unsafe_allow_html=True)
    
    
    st.markdown("---")
    st.markdown("### 💬 AI Assistant")
    if st.button("Chat", key="nav_Chat", use_container_width=True):
        st.session_state.current_page = 'Chat'
        st.rerun()

# =====================================
# Header
# =====================================
st.markdown("""
    <div class="app-header">
        <div class="header-content">
            <h1 class="header-title">Universal Steg Analyzer</h1>
            <p class="header-subtitle">Advanced Multi-Tool Steganography Detection & Analysis Platform</p>
        </div>
    </div>
""", unsafe_allow_html=True)


# =====================================
# Page Router
# =====================================
current_page = st.session_state.current_page

# =====================================
# Helper Function: Organize Signals by Confidence
# =====================================
def display_organized_signals(results_data):
    """Display signals organized by confidence level."""
    
    # Separate by confidence
    strong_signals = [r for r in results_data if r['Confidence'] == 'Strong']
    medium_signals = [r for r in results_data if r['Confidence'] == 'Medium']
    weak_signals = [r for r in results_data if r['Confidence'] == 'Weak']
    
    # Display Strong Signals
    if strong_signals:
        st.markdown(f"""
            <div class="signal-section">
                <div class="signal-header">
                    <div class="signal-title">🚨 Strong Signals</div>
                    <div class="signal-count">{len(strong_signals)}</div>
                </div>
                <div class="signal-body">
        """, unsafe_allow_html=True)
        
        for signal in strong_signals:
            st.markdown(f"""
                <div class="signal-item strong">
                    <div class="signal-meta">
                        <span class="signal-tool">{signal['Tool']}</span>
                        <span class="signal-layer">{signal['Layer']}</span>
                        <span class="signal-confidence strong">STRONG</span>
                    </div>
                    <div class="signal-interpretation">{signal['Interpretation']}</div>
                    <div class="signal-payload-preview">{signal['Payload']}</div>
                </div>
            """, unsafe_allow_html=True)
            
            with st.expander(f"View Full Payload - {signal['Tool']}"):
                st.code(signal['Full_Payload'], language="text")
        
        st.markdown("</div></div>", unsafe_allow_html=True)
    
    # Display Medium Signals
    if medium_signals:
        st.markdown(f"""
            <div class="signal-section">
                <div class="signal-header">
                    <div class="signal-title">⚠️ Medium Signals</div>
                    <div class="signal-count">{len(medium_signals)}</div>
                </div>
                <div class="signal-body">
        """, unsafe_allow_html=True)
        
        for signal in medium_signals:
            st.markdown(f"""
                <div class="signal-item medium">
                    <div class="signal-meta">
                        <span class="signal-tool">{signal['Tool']}</span>
                        <span class="signal-layer">{signal['Layer']}</span>
                        <span class="signal-confidence medium">MEDIUM</span>
                    </div>
                    <div class="signal-interpretation">{signal['Interpretation']}</div>
                    <div class="signal-payload-preview">{signal['Payload']}</div>
                </div>
            """, unsafe_allow_html=True)
            
            with st.expander(f"View Full Payload - {signal['Tool']}"):
                st.code(signal['Full_Payload'], language="text")
        
        st.markdown("</div></div>", unsafe_allow_html=True)
    
    # Display Weak Signals (collapsed by default)
    if weak_signals:
        with st.expander(f"🔍 Weak Signals ({len(weak_signals)}) - Click to expand"):
            for signal in weak_signals:
                st.markdown(f"""
                    <div class="signal-item weak">
                        <div class="signal-meta">
                            <span class="signal-tool">{signal['Tool']}</span>
                            <span class="signal-layer">{signal['Layer']}</span>
                            <span class="signal-confidence weak">WEAK</span>
                        </div>
                        <div class="signal-interpretation">{signal['Interpretation']}</div>
                        <div class="signal-payload-preview">{signal['Payload']}</div>
                    </div>
                """, unsafe_allow_html=True)
                
                with st.expander(f"View Full Payload - {signal['Tool']}"):
                    st.code(signal['Full_Payload'], language="text")

# =====================================
# ANALYZE PAGE - Enhanced with Deep Learning
# =====================================
if current_page == 'Analyze':
    st.markdown('<h2 class="section-header">🔬 Advanced Steganography Detection</h2>', unsafe_allow_html=True)
    
    st.markdown("""
        <div class="alert-box alert-info">
            <span class="alert-icon">i</span>
            <div>
                <strong>Enhanced Detection Mode:</strong> This tool uses multiple detection methods including:
                <ul style="margin: 0.5rem 0 0 1rem; padding: 0; list-style-type: disc;">
                    <li><strong>Deep Learning (CNN)</strong> - SRNet for JPEG steganography</li>
                    <li><strong>Chi-Square Attack</strong> - Statistical LSB detection</li>
                    <li><strong>DCT Analysis</strong> - JPEG coefficient inspection</li>
                    <li><strong>StegExpose</strong> - LSB fusion detection (PNG)</li>
                </ul>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Upload an image to analyze",
        type=["png", "jpg", "jpeg"],
        help="Supported formats: PNG, JPEG",
    )
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        file_size = len(uploaded_file.getvalue())
        width, height = image.size
        fmt = image.format or "Unknown"
        is_jpeg = fmt.upper() in ['JPEG', 'JPG']
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("#### 📷 Image Preview")
            st.image(image, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("#### 📋 Image Information")
            
            format_badge = "🖼️ JPEG" if is_jpeg else "🎨 PNG"
            analysis_type = "DCT + Chi-Square + Deep Learning" if is_jpeg else "LSB + StegExpose"
            
            st.markdown(f"""
                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-label">Format</div>
                        <div class="metric-value dynamic">{format_badge}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Size (KB)</div>
                        <div class="metric-value dynamic">{file_size / 1024:.1f}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Dimensions</div>
                        <div class="metric-value dynamic">{width}x{height}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">Analysis</div>
                        <div class="metric-value dynamic" style="font-size: clamp(0.7rem, 1.5vw, 0.85rem);">{analysis_type}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Analysis options
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### ⚙️ Analysis Options")
        
        col1, col2 = st.columns(2)
        with col1:
            run_deep = st.checkbox("Deep Learning / Statistical", value=True, 
                                   help="CNN-based detection for JPEG, statistical for PNG")

        with col2:
            run_stegexp = st.checkbox("StegExpose", value=True,
                                     help="Statistical fusion LSB detection")
        st.markdown('</div>', unsafe_allow_html=True)
        run_rs = False
        run_spa = False
        
        if st.button("🚀 Start Comprehensive Analysis", use_container_width=True):
            with st.spinner("Analyzing image with multiple detection methods..."):
                # Save temp file
                temp_path = os.path.join(tempfile.gettempdir(), uploaded_file.name)
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Store all results
                all_results = {}
                
                # 1. Statistical suspicion analysis
                status_text.text("🔍 Running statistical suspicion analysis...")
                progress_bar.progress(10)
                suspicion_result = analyze_image_suspicion(temp_path, fmt)
                all_results['suspicion'] = suspicion_result
                
                # 2. StegExpose (PNG focus)
                if run_stegexp:
                    status_text.text("📊 Running StegExpose LSB detection...")
                    progress_bar.progress(25)
                    stegexpose_result = run_stegexpose(temp_path)
                    all_results['stegexpose'] = stegexpose_result
                
                # 3. Deep Learning / Statistical JPEG Analysis
                if run_deep:
                    if is_jpeg:
                        status_text.text("🧠 Running Deep Learning / JPEG Statistical Analysis...")
                    else:
                        status_text.text("🔬 Running LSB Analysis...")
                    progress_bar.progress(45)
                    deep_result = run_deep_steganalysis(temp_path)
                    all_results['deep_learning'] = deep_result
                
                
                # Calculate overall confidence
                status_text.text("📝 Calculating confidence scores...")
                progress_bar.progress(90)
                
                detection_results = {k: v for k, v in all_results.items() 
                                    if k not in ['suspicion']}
                overall = calculate_overall_detection_confidence(detection_results)
                
                progress_bar.progress(100)
                status_text.text("✅ Analysis complete!")
                
                # =====================================
                # Display Results
                # =====================================
                
                st.markdown('<h3 class="section-header">📊 Detection Summary</h3>', unsafe_allow_html=True)
                
                conf_value = overall['overall_confidence']
                conf_level = overall['level']
                conf_color = overall['color']
                
                # Main confidence card with animated meter
                st.markdown(f"""
                    <div class="confidence-meter">
                        <div class="confidence-value">{conf_value:.1f}%</div>
                        <div class="confidence-label">{conf_level}</div>
                        <div class="progress-container" style="margin-top: 1rem;">
                            <div class="progress-bar" style="width: {conf_value}%; transition: width 1s ease;"></div>
                        </div>
                        <div style="margin-top: 0.5rem; font-size: 0.9rem; color: var(--text-tertiary);">
                            {overall['methods_used']} detection methods used
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                # Alert box
                alert_icon = "🚨" if conf_color == 'strong' else "⚠️" if conf_color == 'medium' else "✅"
                st.markdown(f"""
                    <div class="alert-box alert-{conf_color}">
                        <span class="alert-icon">{alert_icon}</span>
                        <div><strong>{overall['message']}</strong></div>
                    </div>
                """, unsafe_allow_html=True)
                
                # =====================================
                # Method Results Grid
                # =====================================
                
                st.markdown('<h3 class="section-header">🔬 Detection Methods</h3>', unsafe_allow_html=True)
                
                # Create columns for results
                num_methods = sum([
                    1,  # Suspicion always runs
                    1 if run_stegexp else 0,
                    1 if run_deep else 0
                ])
                
                cols = st.columns(min(num_methods, 4))
                col_idx = 0
                
                # Suspicion Analysis
                with cols[col_idx % len(cols)]:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.markdown("#### 📉 Statistical Suspicion")
                    st.metric("Score", f"{suspicion_result['suspicion_score']}")
                    st.markdown(f"**Level:** {suspicion_result['level']}")
                    st.markdown(f"**Indicators:** {len(suspicion_result['indicators'])}")
                    st.markdown('</div>', unsafe_allow_html=True)
                col_idx += 1
                
                # StegExpose
                if run_stegexp and 'stegexpose' in all_results:
                    with cols[col_idx % len(cols)]:
                        st.markdown('<div class="card">', unsafe_allow_html=True)
                        st.markdown("#### 🔍 StegExpose")
                        result = all_results['stegexpose']
                        if result.get('success'):
                            st.metric("Confidence", f"{result['confidence']:.1f}%")
                            status = '🔴 Detected' if result.get('is_stego') else '🟢 Clean'
                            st.markdown(f"**Status:** {status}")
                            st.markdown(f"**Type:** {result.get('method_type', 'LSB Fusion')}")
                        else:
                            st.warning(result.get('error', 'Not available'))
                        st.markdown('</div>', unsafe_allow_html=True)
                    col_idx += 1
                
                # Deep Learning / Statistical
                if run_deep and 'deep_learning' in all_results:
                    with cols[col_idx % len(cols)]:
                        st.markdown('<div class="card">', unsafe_allow_html=True)
                        title = "🧠 Deep Learning" if is_jpeg else "🔬 LSB Analysis"
                        st.markdown(f"#### {title}")
                        result = all_results['deep_learning']
                        if result.get('success'):
                            st.metric("Confidence", f"{result['confidence']:.1f}%")
                            status = '🔴 Detected' if result.get('is_stego') else '🟢 Clean'
                            st.markdown(f"**Status:** {status}")
                            st.markdown(f"**Type:** {result.get('method_type', 'N/A')}")
                        else:
                            st.warning(result.get('error', 'Not available'))
                        st.markdown('</div>', unsafe_allow_html=True)
                    col_idx += 1
                
                
                # =====================================
                # Detailed Results (Expandable)
                # =====================================
                
                st.markdown('<h3 class="section-header">📋 Detailed Results</h3>', unsafe_allow_html=True)
                
                # Suspicion Details
                with st.expander("📉 Statistical Suspicion Analysis Details"):
                    st.markdown(f"**Level:** {suspicion_result['level']}")
                    st.markdown(f"**Score:** {suspicion_result['suspicion_score']}")
                    
                    if suspicion_result['indicators']:
                        st.markdown("**Indicators Found:**")
                        for indicator in suspicion_result['indicators']:
                            st.markdown(f"- {indicator}")
                    
                    st.markdown("**Analysis Details:**")
                    st.json(suspicion_result.get('details', {}))
                
                # StegExpose Output
                if run_stegexp and all_results.get('stegexpose', {}).get('success'):
                    with st.expander("🔍 StegExpose Raw Output"):
                        result = all_results['stegexpose']
                        st.markdown(f"**Interpretation:** {result.get('interpretation', 'N/A')}")
                        if result.get('estimated_bytes'):
                            st.markdown(f"**Estimated Hidden Data:** {result['estimated_bytes']} bytes")
                        st.code(result.get('raw_output', 'No output'), language="text")
                
                # Deep Learning / Statistical Output
                if run_deep and all_results.get('deep_learning', {}).get('success'):
                    deep = all_results['deep_learning']
                    with st.expander("🧠 Deep Learning / Statistical Analysis Details"):
                        st.markdown(f"**Method:** {deep.get('method_type', 'N/A')}")
                        st.markdown(f"**Interpretation:** {deep.get('interpretation', 'N/A')}")
                        st.code(deep.get('raw_output', 'No output'), language="text")
                        
                        # If JPEG, show additional details
                        if deep.get('details'):
                            st.markdown("**Sub-Analysis Results:**")
                            for method, result in deep['details'].items():
                                if isinstance(result, dict):
                                    st.markdown(f"- **{method}:** {result.get('interpretation', 'N/A')}")
                
                
                # =====================================
                # Summary Card
                # =====================================
                
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.markdown("#### 📝 Analysis Summary")
                
                if conf_level == "HIGH":
                    st.markdown("🚨 **High probability of steganography detected!**")
                    st.markdown("Multiple detection methods indicate hidden data is present.")
                elif conf_level == "MEDIUM":
                    st.markdown("⚠️ **Possible steganography detected.**")
                    st.markdown("Some indicators suggest hidden data may be present.")
                else:
                    st.markdown("✅ **Image appears clean.**")
                    st.markdown("No significant steganography indicators found.")
                
                st.markdown("")
                st.markdown(f"**Detection Methods Used:** {overall['methods_used']}")
                st.markdown(f"**Overall Confidence:** {conf_value:.1f}%")
                st.markdown(f"**Image Type:** {'JPEG (DCT-based)' if is_jpeg else 'PNG (Lossless)'}")
                st.markdown('</div>', unsafe_allow_html=True)

# =====================================
# DECODE PAGE
# =====================================
elif current_page == 'Decode':
    st.markdown('<h2 class="section-header">🔓 Steganography Extraction</h2>', unsafe_allow_html=True)
    
    st.markdown("""
        <div class="alert-box alert-info">
            <span class="alert-icon">i</span>
            <div>
                <strong>Extraction Mode:</strong> Attempt to extract hidden data using multiple steganography tools.
                Use manual inspection tools to examine metadata and embedded files separately.
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Upload an image to extract data from",
        type=["png", "jpg", "jpeg"],
        help="Upload a steganographic image",
        key="decode_upload"
    )
    
    if uploaded_file:
        col1, col2 = st.columns([1, 1.5])
        
        with col1:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("#### 📷 Image Preview")
            st.image(Image.open(uploaded_file), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("#### ⚙️ Extraction Settings")
            
            password = st.text_input("Password (if required)", type="password", placeholder="Leave empty if no password")
            
            tool_selection = st.multiselect(
                "Select extraction tools",
                ["Zsteg", "Steghide", "OutGuess", "OpenStego", "Jsteg", "F5"],
                default=["Zsteg", "Steghide"]
            )
            
            st.markdown("---")
            st.markdown("#### 🔍 Manual Inspection Tools")
            st.markdown("*These tools inspect file structure but are not counted as signals*")
            
            inspect_exif = st.checkbox("ExifTool (Metadata)", value=True)
            inspect_binwalk = st.checkbox("Binwalk (Embedded Files)", value=True)
            inspect_trailer = st.checkbox("Trailer Analysis", value=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("🔓 Extract Data", use_container_width=True):
            with st.spinner("Running extraction tools..."):
                # Save temp file
                temp_path = os.path.join(tempfile.gettempdir(), uploaded_file.name)
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                image = Image.open(temp_path)
                fmt = image.format or "Unknown"
                
                all_results = []
                
                progress = st.progress(0)
                total_tools = len(tool_selection) + sum([inspect_exif, inspect_binwalk, inspect_trailer])
                current = 0
                
                # Run selected extraction tools
                for tool in tool_selection:
                    current += 1
                    progress.progress(current / total_tools)
                    
                    if tool == "Zsteg":
                        raw, rows = run_zsteg(temp_path)
                        all_results.extend(rows)
                    elif tool == "Steghide":
                        raw, rows = run_steghide(temp_path, password)
                        all_results.extend(rows)
                    elif tool == "OutGuess":
                        raw, rows = run_outguess(temp_path)
                        all_results.extend(rows)
                    elif tool == "OpenStego":
                        raw, rows = run_openstego(temp_path, password)
                        all_results.extend(rows)
                    elif tool == "Jsteg":
                        raw, rows = run_jsteg(temp_path)
                        all_results.extend(rows)
                    elif tool == "F5":
                        raw, rows = run_f5(temp_path, password if password else "abc123")
                        all_results.extend(rows)
                
                progress.progress(1.0)
                
                # Display extraction results
                st.markdown('<h3 class="section-header">📤 Extraction Results</h3>', unsafe_allow_html=True)
                
                if all_results:
                    display_organized_signals(all_results)
                else:
                    st.markdown("""
                        <div class="alert-box alert-weak">
                            <span class="alert-icon">✓</span>
                            <div><strong>No hidden data found</strong> with the selected extraction tools.</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                # Manual inspection results
                if inspect_exif or inspect_binwalk or inspect_trailer:
                    st.markdown('<h3 class="section-header">🔍 Manual Inspection</h3>', unsafe_allow_html=True)
                    
                    if inspect_exif:
                        raw_exif, exif_rows = run_exiftool(temp_path)
                        with st.expander("📋 ExifTool Metadata"):
                            if raw_exif:
                                st.code(raw_exif, language="text")
                            else:
                                st.info("No metadata found or ExifTool not available.")
                    
                    if inspect_binwalk:
                        raw_binwalk, binwalk_rows = run_binwalk(temp_path)
                        with st.expander("📦 Binwalk Analysis"):
                            if raw_binwalk:
                                st.code(raw_binwalk, language="text")
                                if binwalk_rows:
                                    st.warning("Embedded files detected!")
                            else:
                                st.info("No embedded files found or Binwalk not available.")
                    
                    if inspect_trailer:
                        trailer_rows = check_trailer_manual(temp_path, fmt)
                        with st.expander("📄 Trailer Analysis"):
                            if trailer_rows:
                                for row in trailer_rows:
                                    st.warning(f"Data found: {row['Interpretation']}")
                                    st.code(row['Payload'], language="text")
                            else:
                                st.info("No trailer data found.")

# =====================================
# ENCODE PAGE
# =====================================
elif current_page == 'Encode':
    st.markdown('<h2 class="section-header">🔒 Steganography Encoding</h2>', unsafe_allow_html=True)
    
    st.markdown("""
        <div class="alert-box alert-info">
            <span class="alert-icon">i</span>
            <div>
                <strong>Encoding Mode:</strong> Hide secret data within an image using steganography.
                The output image will look identical to the original but contain hidden data.
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 📷 Upload Cover Image")
        cover_image = st.file_uploader("Cover image", type=["png", "jpg", "jpeg"], key="encode_cover")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 📝 Secret Data")
        secret_data = st.text_area("Enter secret message", height=150, placeholder="Type your secret message here...")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### ⚙️ Encoding Settings")
    
    col1, col2 = st.columns(2)
    with col1:
        encoding_method = st.selectbox("Encoding method", ["Steghide", "OpenStego"])
    with col2:
        encode_password = st.text_input("Password (optional)", type="password", key="encode_password")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if cover_image and secret_data:
        if st.button("🔒 Embed Data", use_container_width=True):
            with st.spinner("Embedding data..."):
                temp_cover = os.path.join(tempfile.gettempdir(), cover_image.name)
                with open(temp_cover, "wb") as f:
                    f.write(cover_image.getbuffer())
                
                if encoding_method == "Steghide":
                    result = encode_steghide(temp_cover, secret_data, encode_password)
                else:
                    result = encode_openstego(temp_cover, secret_data, encode_password)
                
                if result['success']:
                    st.markdown("""
                        <div class="alert-box alert-weak">
                            <span class="alert-icon">✓</span>
                            <div><strong>Success:</strong> Data embedded successfully.</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    with open(result['output_path'], 'rb') as f:
                        st.download_button(
                            "📥 Download Steganographic Image",
                            f,
                            file_name=os.path.basename(result['output_path']),
                            mime="image/png",
                            use_container_width=True
                        )
                else:
                    st.markdown(f"""
                        <div class="alert-box alert-strong">
                            <span class="alert-icon">✗</span>
                            <div><strong>Error:</strong> {result.get('error', 'Unknown error')}</div>
                        </div>
                    """, unsafe_allow_html=True)

# =====================================
# CHAT PAGE
# =====================================
elif current_page == 'Chat':
    st.markdown('<h2 class="section-header">💬 AI Cryptography Assistant</h2>', unsafe_allow_html=True)
    
    st.markdown("""
        <div class="alert-box alert-info">
            <span class="alert-icon">i</span>
            <div>
                <strong>AI Assistant:</strong> Ask me about steganography techniques, cryptographic concepts, or how to interpret analysis results. 
                Make sure to set your Gemini API key in the sidebar first.
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    if not st.session_state.gemini_api_key:
        st.markdown("""
            <div class="alert-box alert-medium">
                <span class="alert-icon">⚠</span>
                <div>
                    <strong>API Key Required:</strong> Please enter your Gemini API key in the sidebar to use the chatbot.
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 🤖 Chat with AI Assistant")
    
    # Display chat messages
    if st.session_state.chat_messages:
        st.markdown("---")
        chat_container = st.container()
        with chat_container:
            for i, msg in enumerate(st.session_state.chat_messages):
                if msg['role'] == 'user':
                    st.markdown(f'<div class="chat-message user"><div class="chat-bubble user">{msg["content"]}</div></div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-message"><div class="chat-bubble assistant">{msg["content"]}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align: center; padding: 2rem; color: var(--text-tertiary);">
            <p>Start a conversation by asking a question below!</p>
            <p style="margin-top: 1rem; font-size: 0.9rem;">Example: "What is LSB steganography?"</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Chat input
    st.markdown("---")
    user_message = st.text_input("Ask a question...", key="chat_input", placeholder="e.g., What is LSB steganography? How does zsteg work?")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("Send", key="send_chat", use_container_width=True):
            if user_message:
                if not st.session_state.gemini_api_key:
                    st.error("Please set your Gemini API key in the sidebar first.")
                else:
                    st.session_state.chat_messages.append({"role": "user", "content": user_message})
                    response = send_to_gemini(user_message, st.session_state.gemini_api_key)
                    st.session_state.chat_messages.append({"role": "assistant", "content": response})
                    st.rerun()
    with col2:
        if st.button("Clear", key="clear_chat", use_container_width=True):
            st.session_state.chat_messages = []
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Example questions
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 💡 Example Questions")
    st.markdown("""
    - **"What is LSB steganography?"**
    - **"How does zsteg detect hidden data?"**
    - **"What are B1, B2, B3, B4 channels?"**
    - **"Explain DCT-based steganography"**
    - **"What's the difference between Steghide and OpenStego?"**
    - **"How do I interpret strong vs weak signals?"**
    - **"What is Chi-Square attack in steganalysis?"**
    """)
    st.markdown('</div>', unsafe_allow_html=True)

# =====================================
# ABOUT PAGE
# =====================================
elif current_page == 'About':
    st.markdown('<h2 class="section-header">ℹ️ About This Tool</h2>', unsafe_allow_html=True)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### Purpose")
    st.markdown("Universal Steg Analyzer is a comprehensive steganography detection and analysis platform that combines multiple detection methods, statistical analysis, and deep learning to identify hidden data in images.")
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 🔍 Extraction Tools")
        st.markdown("Tools that detect and extract hidden data:")
        st.markdown("""
        - **Zsteg** - PNG LSB analysis with B1-B4 detection
        - **Steghide** - JPG/BMP extraction
        - **OutGuess** - Statistical steganography
        - **OpenStego** - LSB embedding detection
        - **Jsteg** - JPEG steganography
        - **F5** - Advanced JPEG detection
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 📊 Statistical Analysis")
        st.markdown("Advanced detection methods:")
        st.markdown("""
        - **StegExpose** - LSB fusion detection
        - **Chi-Square Attack** - PoV statistical analysis
        - **DCT Analysis** - JPEG coefficient inspection
        - **Deep Learning** - CNN-based detection
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 🆕 New Features (v4.0)")
    st.markdown("""
    - ✓ **Deep Learning Detection** - SRNet CNN for JPEG steganography
    - ✓ **Chi-Square Attack** - Statistical LSB detection
    - ✓ **DCT Coefficient Analysis** - Detects F5 shrinkage patterns
    - ✓ **Format-Aware Analysis** - Different methods for JPEG vs PNG
    - ✓ **Comprehensive Results** - Detailed per-method breakdown
    - ✓ Enhanced UI with method selection options
    """)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 📋 Detection Method Details")
    
    st.markdown("**Chi-Square Attack:**")
    st.markdown("Analyzes pairs of pixel values (2i, 2i+1). Natural images have unequal pair counts; LSB embedding equalizes them.")
    
    st.markdown("**DCT Analysis:**")
    st.markdown("Examines JPEG DCT coefficients. F5 steganography causes 'shrinkage' (more zeros).")
    
    st.markdown("**Deep Learning (SRNet):**")
    st.markdown("12-layer residual CNN that learns steganographic artifacts. Best for J-UNIWARD, nsF5, UERD.")
    st.markdown('</div>', unsafe_allow_html=True)

# =====================================
# Footer
# =====================================
st.markdown("""
    <div class="custom-footer">
        <p>Universal Steg Analyzer v4.0 | Enhanced with Deep Learning</p>
        <p style="font-size: 0.85rem; margin-top: 0.5rem;">Advanced Steganography Detection & Analysis Platform</p>
    </div>
""", unsafe_allow_html=True)