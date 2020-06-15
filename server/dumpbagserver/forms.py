from wtforms import Form, StringField
from wtforms.validators import DataRequired, Length, Regexp


class SearchForm(Form):
    search = StringField(
        "Search",
        validators=[
            DataRequired(),
            Regexp(r"^[\w-]+$", message="Only letters,numbers,_,-."),
            Length(min=2, max=64),
        ],
    )
