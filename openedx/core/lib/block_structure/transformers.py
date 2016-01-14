"""
Module for a collection of BlockStructureTransformers.
"""
from logging import getLogger

from .exceptions import TransformerException
from .transformer_registry import TransformerRegistry


logger = getLogger(__name__)  # pylint: disable=C0103


class BlockStructureTransformers(object):
    """
    Class for a collection of block structure transformers.
    """
    def __init__(self, transformers=None, usage_info=None):
        """
        Arguments:
            transformers ([BlockStructureTransformer]) - List of transformers
                to add to the collection.

            usage_info (any negotiated type) - A usage-specific object
                that is passed to the block_structure and forwarded to all
                requested Transformers in order to apply a
                usage-specific transform. For example, an instance of
                usage_info would contain a user object for which the
                transform should be applied.

        Raises:
            TransformerException - if any transformer is not registered in the
                Transformer Registry.
        """
        self.usage_info = usage_info
        self.transformers = []
        if transformers:
            self.add(transformers)

    def add(self, transformers):
        """
        Adds the given transformers to the collection.

        Args:
            transformers ([BlockStructureTransformer]) - List of transformers
                to add to the collection.

        Raises:
            TransformerException - if any transformer is not registered in the
                Transformer Registry.
        """
        unregistered_transformers = TransformerRegistry.find_unregistered(transformers)
        if unregistered_transformers:
            raise TransformerException(
                "The following requested transformers are not registered: {}".format(unregistered_transformers)
            )

        self.transformers.extend(transformers)

    @classmethod
    def collect(cls, block_structure):
        """
        Collects data for each registered transformer.
        """
        for transformer in TransformerRegistry.get_registered_transformers():
            block_structure._add_transformer(transformer)  # pylint: disable=protected-access
            transformer.collect(block_structure)

        # Collect all fields that were requested by the transformers.
        block_structure._collect_requested_xblock_fields()  # pylint: disable=protected-access

    def transform(self, block_structure):
        """
        The given block structure is transformed by each transformer in the
        collection, in the order that the transformers were added.
        """
        for transformer in self.transformers:
            transformer.transform(self.usage_info, block_structure)

        # Prune the block structure to remove any unreachable blocks.
        block_structure._prune_unreachable()  # pylint: disable=protected-access

    @classmethod
    def is_collected_outdated(cls, block_structure):
        """
        Returns whether the collected data in the block structure is outdated.
        """
        outdated_transformers = []
        for transformer in TransformerRegistry.get_registered_transformers():
            version_in_block_structure = block_structure._get_transformer_data_version(transformer)  # pylint: disable=protected-access
            if transformer.VERSION != version_in_block_structure:
                outdated_transformers.append(transformer)

        if outdated_transformers:
            logger.debug(
                "Collected Block Structure data for the following transformers is outdated: '%s'.",
                [(transformer.name(), transformer.VERSION) for transformer in outdated_transformers],
            )

        return bool(outdated_transformers)
