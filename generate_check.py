from PIL import Image, ImageDraw, ImageFont

W, H = (600,400)
msg = "V-12"

im = Image.new("RGBA",(W,H),"white")
draw = ImageDraw.Draw(im)
myFont = ImageFont.truetype("DejaVuSans-Bold.ttf", 200)
w, h = draw.textsize(msg, font=myFont)
ratio = 500.0 / w
new_font_size = 200 * ratio
myFont = ImageFont.truetype("DejaVuSans-Bold.ttf", int(new_font_size))
w, h = draw.textsize(msg, font=myFont)

draw.text(((W-w)/2,(H-h)/2), msg, fill="black", font=myFont)

im.save("check.png", "PNG")