"""Package import stays healthy before the models grow."""


def test_package_imports():
    import pyoptionpricing

    assert pyoptionpricing.OptionFactory.registered()
