"""
For use with websocket server.
"""

from datetime import datetime
from web3 import Web3

from ..app import App
from ..src.order_enums import OrderSource, OrderState
from ..src.order_hash import make_order_hash
from ..src.utils import parse_insert_status
from ..tasks.update_order import update_order_by_signature

INSERT_ORDER_STMT = """
    INSERT INTO orders
    (
        "source", "signature",
        "token_give", "amount_give", "token_get", "amount_get", "available_volume",
        "expires", "nonce", "user", "state", "v", "r", "s", "date"
    )
    VALUES ($1, $2, $3, $4, $5, $6, $6, $7, $8, $9, $10, $11, $12, $13, $14)
    ON CONFLICT ON CONSTRAINT index_orders_on_signature DO NOTHING
"""
async def record_order(order):
    signature = make_order_hash(order)
    insert_args = (
        OrderSource.OFFCHAIN.name,
        Web3.toBytes(hexstr=signature),
        Web3.toBytes(hexstr=order["tokenGive"]),
        order["amountGive"],
        Web3.toBytes(hexstr=order["tokenGet"]),
        order["amountGet"],
        order["expires"],
        order["nonce"],
        Web3.toBytes(hexstr=order["user"]),
        OrderState.OPEN.name,
        order["v"],
        order["r"],
        order["s"],
        datetime.utcnow()
    )

    async with App().db.acquire_connection() as connection:
        insert_retval = await connection.execute(INSERT_ORDER_STMT, *insert_args)
        _, _, did_insert = parse_insert_status(insert_retval)
    return did_insert
