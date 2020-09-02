from ...utils.address_util.format_address import format_address
from ocr_structuring.utils.logging import logger
from ...utils import bk_tree


class CarMixin(object):

    def _handle_address(self, structure_items, fg_items, key='address'):
        """
        处理地址
        :param structure_items:
        :param fg_items:
        :return:
        """
        address = structure_items[key].content
        new_address = format_address(address)
        if new_address != address:
            logger.debug('change province {} to {}'.format(address, new_address))
            structure_items[key].content = new_address
