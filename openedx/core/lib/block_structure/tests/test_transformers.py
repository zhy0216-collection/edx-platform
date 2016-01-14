"""
Tests for transformers.py
"""
from mock import MagicMock, patch
from unittest import TestCase

from ..block_structure import BlockStructureModulestoreData
from ..exceptions import TransformerException
from ..transformers import BlockStructureTransformers
from .test_utils import (
    ChildrenMapTestMixin, MockTransformer, mock_registered_transformers
)


class TestBlockStructureTransformers(ChildrenMapTestMixin, TestCase):
    """
    Test class for testing BlockStructureTransformers
    """
    class UnregisteredTransformer(MockTransformer):
        """
        Mock transformer that is not registered.
        """
        pass

    def setUp(self):
        super(TestBlockStructureTransformers, self).setUp()
        self.transformers = BlockStructureTransformers(usage_info=MagicMock())
        self.registered_transformers = [MockTransformer]

    def add_mock_transformer(self):
        """
        Adds the registered transformers to the self.transformers collection.
        """
        with mock_registered_transformers(self.registered_transformers):
            self.transformers.add(self.registered_transformers)

    def test_add_registered(self):
        self.add_mock_transformer()
        self.assertIn(MockTransformer, self.transformers.transformers)

    def test_add_unregistered(self):
        with self.assertRaises(TransformerException):
            self.transformers.add([self.UnregisteredTransformer])

        self.assertEquals(self.transformers.transformers, [])

    def test_collect(self):
        with mock_registered_transformers(self.registered_transformers):
            with patch(
                'openedx.core.lib.block_structure.tests.test_utils.MockTransformer.collect'
            ) as mock_collect_call:
                self.transformers.collect(block_structure=MagicMock())
                self.assertTrue(mock_collect_call.called)

    def test_transform(self):
        self.add_mock_transformer()

        with patch(
            'openedx.core.lib.block_structure.tests.test_utils.MockTransformer.transform'
        ) as mock_transform_call:
            self.transformers.transform(block_structure=MagicMock())
            self.assertTrue(mock_transform_call.called)

    def test_is_collected_outdated(self):
        block_structure = self.create_block_structure(
            self.SIMPLE_CHILDREN_MAP,
            BlockStructureModulestoreData
        )

        with mock_registered_transformers(self.registered_transformers):
            self.assertTrue(self.transformers.is_collected_outdated(block_structure))
            self.transformers.collect(block_structure)
            self.assertFalse(self.transformers.is_collected_outdated(block_structure))
