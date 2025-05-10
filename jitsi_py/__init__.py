try:
    from .version import __version__
except ImportError:
    try:
        from setuptools_scm import get_version
        __version__ = get_version(root='..', relative_to=__file__)
    except (ImportError, LookupError):
        __version__ = "2.0.1"
        __author__ = "Kumar Abhishek"
        __description__ = "Python integration for Jitsi Meet"
        __url__ = ""
        __email__ = "developer@kabhishek18.com"
        __license__ = "MIT"