import numpy as np
import scipy.stats as stats
import plotly.graph_objects as go
import pandas as pd

def calculate_spc_stats(measurements: list[float], nominal: float, li: float, ls: float):
    """
    Calculates historical SPC statistics for a set of measurements.
    Returns:
      - mean (X-barra)
      - std (sigma)
      - cp
      - cpk
      - status_desc
    """
    if len(measurements) < 2:
        return {
            "mean": np.mean(measurements) if measurements else 0.0,
            "std": 0.0,
            "cp": None,
            "cpk": None,
            "status_desc": "Datos Insuficientes (<2)",
            "pasa": True
        }
        
    mean = float(np.mean(measurements))
    std = float(np.std(measurements, ddof=1)) # Sample standard deviation
    
    if std == 0:
        return {
            "mean": mean,
            "std": 0.0,
            "cp": None,
            "cpk": None,
            "status_desc": "Variabilidad Cero",
            "pasa": True
        }
        
    cp = (ls - li) / (6 * std)
    cpu = (ls - mean) / (3 * std)
    cpl = (mean - li) / (3 * std)
    cpk = min(cpu, cpl)
    
    # Process capability status description
    if cpk >= 1.33:
        status_desc = "Proceso Capaz (Excelente) ✔"
        pasa = True
    elif cpk >= 1.0:
        status_desc = "Proceso Aceptable ⚠"
        pasa = True
    else:
        status_desc = "Proceso No Capaz (Fuera de Control) ✘"
        pasa = False
        
    return {
        "mean": mean,
        "std": std,
        "cp": cp,
        "cpk": cpk,
        "status_desc": status_desc,
        "pasa": pasa
    }

def generate_gauss_chart(measurements: list[float], nominal: float, li: float, ls: float, title_text: str):
    """
    Generates an interactive Plotly chart showing:
      1. Normal Distribution curve of the measurements (historical or current)
      2. L.I. (LSL) and L.S. (USL) limits
      3. Nominal value
      4. Current shift values as individual markers on the X axis
    """
    fig = go.Figure()
    
    # Convert inputs to float
    nominal = float(nominal)
    li = float(li)
    ls = float(ls)
    
    # Default range for X axis plotting
    # Pad limits slightly to show context
    margin = (ls - li) * 0.5 if (ls - li) > 0 else 0.5
    x_min = li - margin
    x_max = ls + margin
    
    # Create normal distribution curve if we have enough points
    if len(measurements) >= 2:
        mean = np.mean(measurements)
        std = np.std(measurements, ddof=1)
        if std > 0:
            x_vals = np.linspace(x_min, x_max, 200)
            y_vals = stats.norm.pdf(x_vals, mean, std)
            
            # Plot normal distribution line
            fig.add_trace(go.Scatter(
                x=x_vals, y=y_vals,
                mode='lines',
                name='Distribución Real',
                line=dict(color='#0056b3', width=3),
                fill='tozeroy',
                fillcolor='rgba(0, 86, 179, 0.1)'
            ))
            
            # Add vertical line for calculated mean
            fig.add_vline(
                x=mean, 
                line_dash="dot", 
                line_color="#475569", 
                annotation_text=f"Media: {mean:.4f}",
                annotation_position="bottom right"
            )
    else:
        # If no points, show a default empty space/placeholder
        mean = nominal
        std = (ls - li) / 6.0 if (ls - li) > 0 else 0.1
        x_vals = np.linspace(x_min, x_max, 200)
        y_vals = stats.norm.pdf(x_vals, mean, std)
        fig.add_trace(go.Scatter(
            x=x_vals, y=y_vals,
            mode='lines',
            name='Distribución Nominal (Ideal)',
            line=dict(color='#94a3b8', width=2, dash='dash')
        ))
        
    # Vertical Line: Nominal
    fig.add_vline(
        x=nominal, 
        line_color="#10b981", 
        line_width=2,
        annotation_text=f"Nom: {nominal:.3f}", 
        annotation_position="top left"
    )
    
    # Vertical Line: LSL (L.I.)
    fig.add_vline(
        x=li, 
        line_color="#ef4444", 
        line_width=2, 
        line_dash="dash",
        annotation_text=f"L.I.: {li:.3f}", 
        annotation_position="top left"
    )
    
    # Vertical Line: USL (L.S.)
    fig.add_vline(
        x=ls, 
        line_color="#ef4444", 
        line_width=2, 
        line_dash="dash",
        annotation_text=f"L.S.: {ls:.3f}", 
        annotation_position="top right"
    )
    
    # Current measurements plot (as markers on X axis)
    if measurements:
        y_scatter = [0] * len(measurements)
        fig.add_trace(go.Scatter(
            x=measurements, y=y_scatter,
            mode='markers',
            name='Muestras Actuales',
            marker=dict(color='#f59e0b', size=12, symbol='diamond-open', line=dict(width=2)),
            hovertemplate='Valor: %{x:.4f}'
        ))
        
    fig.update_layout(
        title=dict(
            text=title_text,
            font=dict(size=14, color="#1e293b", family="sans serif")
        ),
        xaxis_title="Dimensión Medida",
        yaxis_title="Densidad de Probabilidad",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=60, b=40),
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(gridcolor='#f1f5f9', zeroline=False),
        yaxis=dict(gridcolor='#f1f5f9', showticklabels=False)
    )
    
    return fig
