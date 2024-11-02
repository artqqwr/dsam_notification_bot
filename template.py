from jinja2 import Environment, FileSystemLoader

from config import TEMPLATES_PATH

env = Environment(
    loader=FileSystemLoader(TEMPLATES_PATH),
)

def render(name: str, *args, **kwargs) -> str:
    template = env.get_template(f'{name}.tmpl')
    return template.render(*args, **kwargs)