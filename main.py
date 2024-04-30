from flask import Flask, render_template
from flask_bootstrap import Bootstrap4
from flask_wtf import FlaskForm
from wtforms import SubmitField, FileField, IntegerField, RadioField
from wtforms.validators import DataRequired, NumberRange
from PIL import Image, ImageEnhance, ImageFilter
import numpy as np
import pandas as pd
from werkzeug.utils import secure_filename
import os

UPLOAD_FOLDER = './static/assets/img/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
PATH = './static/assets/img/sample.jpg'
delta = 1

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap4(app)


class MyForm(FlaskForm):
    file = FileField('File to load', validators=[DataRequired()])
    colors = IntegerField('Number of colors', validators=[NumberRange(min=1)], default=10)
    delta = IntegerField('Delta (1-255)',  validators=[NumberRange(min=1, max=255)], default=24)
    brightness = RadioField('Reduce brightness', choices=['Yes', 'No'], default='No')
    gradient = RadioField('Reduce gradient', choices=['Yes', 'No'], default='No')
    submit = SubmitField('Run')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# array of quantised colors' values
def quantise(img):
    pixel_list = np.array(img).reshape(-1, 3)
    quant_pix = np.vectorize(lambda t: q(t))
    pixels = quant_pix(pixel_list)
    return pixels


# quantisation for each individual colour component of the pixel
# https://medium.com/@muizhassan83/how-to-perform-image-quantisation-4b69c2fd8539
def q(val):
    remainder = val % delta
    quotient = val // delta
    if val < 255:
        return quotient * delta if remainder < delta // 2 or quotient == 5 else (quotient + 1) * delta
    else:
        return (quotient - 1) * delta


def rgb_to_hex(r, g, b):
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)


def get_colors(img, number):
    quantised_pixels = quantise(img)
    df = pd.DataFrame(data=quantised_pixels, columns=['r', 'g', 'b'])
    df.sort_values(['r', 'g', 'b'], inplace=True)
    colors = df.value_counts(normalize=True).to_frame()[:number]
    hex_colors = [["{:.6f}".format(row.proportion), rgb_to_hex(r=index[0], g=index[1], b=index[2])]
                  for (index, row) in colors.iterrows()]
    return hex_colors


@app.route("/", methods=['GET', 'POST'])
def home():
    global delta
    new_form = MyForm()
    file = new_form.file.data
    number_colors = new_form.colors.data
    delta = new_form.delta.data
    if delta > 255 or delta < 0:
        delta = 24

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)

        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)
        with Image.open(file) as img:
            img.load()
    else:
        img = Image.open(PATH)
        path = PATH
    if new_form.brightness.data == "Yes":
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(0.9)
    if new_form.gradient.data == "Yes":
        img = img.filter(ImageFilter.GaussianBlur(radius=2))

    colors = get_colors(img, number=number_colors)

    return render_template('index.html', img=path, colors=colors, form=new_form)


if __name__ == '__main__':
    app.run(debug=True)
