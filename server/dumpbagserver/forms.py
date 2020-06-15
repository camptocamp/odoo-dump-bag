from dumpbagserver import app_config
from wtforms import Form, StringField
from wtforms.validators import DataRequired, Length, Regexp, ValidationError

from .bagger import Bagger


class SearchForm(Form):
    search = StringField(
        "Search",
        validators=[
            DataRequired(),
            Regexp(r"^\w+$", message="Only letters numbers or _."),
            Length(min=2, max=64),
        ],
    )

    def validate_search(form, field):
        bagger = Bagger(app_config)
        dumps = bagger.list_dumps()
        parse = form.search.data
        find = False
        for bds in dumps:
            if parse in bds:
                find = True
        if find is False:
            raise ValidationError(parse + " not in any of the db names.")
