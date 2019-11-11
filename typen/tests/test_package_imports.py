import unittest


class TestPackageImports(unittest.TestCase):
    def test_import_enforce_type_hints(self):
        from typen import enforce_type_hints  # noqa: F401

    def test_import_strict_type_hints(self):
        from typen import strict_type_hints  # noqa: F401
