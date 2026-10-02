from io import BytesIO
from django.template.loader import render_to_string
from weasyprint import HTML


def generar_pdf_factura(factura):
    """
    Genera el PDF de una factura en memoria y retorna bytes.
    """
    from facturacion.models import DetalleVenta
    
    contexto = {
        'factura': factura,
        'detalles': factura.detalles.select_related('producto').all(),
        'cliente': factura.cliente,
        'usuario': factura.usuario,
    }
    
    html_string = render_to_string('facturacion/factura_pdf.html', contexto)
    
    pdf_file = BytesIO()
    HTML(string=html_string).write_pdf(
        pdf_file, 
        base_url=None,  # No necesitamos base_url para PDF adjunto
        presentational_hints=True
    )
    
    pdf_file.seek(0)
    return pdf_file.read()