import io
import base64
import matplotlib.pyplot as plt

def fig_to_base64(fig):
    """Convierte una figura en Base64 para incrustarla directo en el HTML."""
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight')
    buf.seek(0)
    base64_string = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return f"data:image/png;base64,{base64_string}"
