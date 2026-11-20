import sys
import qrcode

# 1. Verificar que se haya pasado una URL como argumento
if len(sys.argv) < 2:
    print("Uso correcto: python generarQR.py <url>")
    sys.exit(1)

# 2. Obtener la URL desde el primer argumento
url = sys.argv[1]

# Asegurar que tenga http/https para que los lectores lo abran como enlace web
if not url.startswith(("http://", "https://")):
    url = "https://" + url

# 3. Generar el código QR
qr = qrcode.QRCode(
    version=1,
    box_size=10,
    border=4,
)
qr.add_data(url)
qr.make(fit=True)

imagen = qr.make_image(fill_color="black", back_color="white")

# 4. Limpiar el nombre de la web para usarlo como nombre de archivo
nombre_limpio = url.replace("https://", "").replace("http://", "").replace("/", "_")
nombre_archivo = f"qr_{nombre_limpio}.png"

# 5. Guardar la imagen en la misma carpeta
imagen.save(nombre_archivo)
print(f"¡Listo! QR guardado como: {nombre_archivo}")
