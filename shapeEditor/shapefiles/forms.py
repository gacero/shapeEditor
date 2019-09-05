from django import forms

class  ImportShapefileForm(forms.Form):
    import_file = forms.FileField(label="Seleccione un shapefile comprimido en Zip")