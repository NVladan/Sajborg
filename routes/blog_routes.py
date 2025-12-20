from flask import Blueprint, render_template, abort
from models import Post

blog_bp = Blueprint('blog', __name__, url_prefix='/tech-magazin')


@blog_bp.route('/')
def posts():
    """Prikazuje sve objavljene blog postove."""
    posts = Post.query.filter_by(is_published=True).order_by(Post.created_at.desc()).all()
    return render_template('blog/posts.html', title='Tech Magazin', posts=posts)


@blog_bp.route('/<string:slug>')
def post_detail(slug):
    """Prikazuje jedan blog post."""
    post = Post.query.filter_by(slug=slug, is_published=True).first()
    if not post:
        abort(404)
    return render_template('blog/post_detail.html', title=post.title, post=post)