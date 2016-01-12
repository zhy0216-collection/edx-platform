"""
Helpers for Course Blocks tests.
"""

from openedx.core.lib.block_structure.cache import BlockStructureCache
from openedx.core.lib.block_structure.transformer_registry import TransformerRegistry
from ..api import _get_cache


class EnableTransformerRegistryMixin(object):
    """
    Mixin that enables the TransformerRegistry to USE_PLUGIN_MANAGER for
    finding registered transformers.
    """
    def setUp(self, **kwargs):
        super(EnableTransformerRegistryMixin, self).setUp(**kwargs)
        TransformerRegistry.USE_PLUGIN_MANAGER = True

    def tearDown(self):
        TransformerRegistry.USE_PLUGIN_MANAGER = False


def is_course_in_block_structure_cache(course_key, store):
    """
    Returns whether the given course is in the Block Structure cache.
    """
    course_usage_key = store.make_course_usage_key(course_key)
    return BlockStructureCache(_get_cache()).get(course_usage_key) is not None
