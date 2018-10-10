from pydaybit.phoenix.exceptions import *


class UnexpectedFormat(Exception):
    pass


class ResponseError(Exception):
    def __init__(self, topic, code):
        msg = "channel:{}, error:{}".format(topic, code)
        super().__init__(msg)


class PrimaryKeyError(Exception):
    pass


# General
class UnauthenticatedError(ResponseError):
    pass


class InvalidArgumentsError(ResponseError):
    pass


class ResourceNotFoundError(ResponseError):
    pass


class InvalidTokenError(ResponseError):
    pass


# Api
class APIInvalidTimestampOrTimeout(ResponseError):
    pass


class APITimeout(ResponseError):
    pass


class APIExceededRateLimit(ResponseError):
    pass


class APIInvalidParamTypes(ResponseError):
    pass


class APIRequiredParamsNotProvided(ResponseError):
    pass


# Order
class OrderExceededVoidRate(ResponseError):
    pass


class OrderExceededMaxOrders(ResponseError):
    pass


class OrderExceededMaxTStops(ResponseError):
    pass


class OrderNotTradableCoin(ResponseError):
    pass


class OrderNotSellableMarket(ResponseError):
    pass


class OrderNotBuyableMarket(ResponseError):
    pass


class OrderViolatesMinUSD(ResponseError):
    pass


class OrderOutOfPriceRange(ResponseError):
    pass


class OrderOutOfStopPriceRange(ResponseError):
    pass


class OrderUnplaceableMakerOnly(ResponseError):
    pass


class OrderUnPlaceableTakerOnly(ResponseError):
    pass


class OrderExceededAssetValues(ResponseError):
    pass


class OrderAlreadyClosed(ResponseError):
    pass


# Wdrl
class WdrlInvalidCoin(ResponseError):
    pass


class WdrlSuspendedCoin(ResponseError):
    pass


class WdrlPrecisionError(ResponseError):
    pass


class WdrlUnderMinAmount(ResponseError):
    pass


class WdrlOverDailyWdrlLimit(ResponseError):
    pass


class WdrlExceededAssetValues(ResponseError):
    pass


class WdrlNeedsToTag(ResponseError):
    pass


class WdrlNeedsToOrg(ResponseError):
    pass


class WdrlInvalidAddr(ResponseError):
    pass


def find_error_types(code):
    switcher = {
        # General
        'unauthenticated': UnauthenticatedError,
        'invalid_arguments': InvalidArgumentsError,
        'resource_not_found': ResourceNotFoundError,
        'invalid_token': InvalidTokenError,

        # API
        'api_invalid_timestamp_or_timeout': APIInvalidTimestampOrTimeout,
        'api_timeout': APITimeout,
        'api_exceeded_rate_limit': APIExceededRateLimit,
        'api_invalid_param_types': APIInvalidParamTypes,
        'api_required_params_not_provided': APIRequiredParamsNotProvided,

        # Order
        'order_exceeded_void_rate': OrderExceededVoidRate,
        'order_exceeded_max_orders': OrderExceededMaxOrders,
        'order_exceeded_max_tstops': OrderExceededMaxTStops,
        'order_not_tradable_coin': OrderNotTradableCoin,
        'order_not_sellable_market': OrderNotSellableMarket,
        'order_not_buyable_market': OrderNotBuyableMarket,
        'order_violates_min_usd': OrderViolatesMinUSD,
        'order_out_of_price_range': OrderOutOfPriceRange,
        'order_out_of_stop_price_range': OrderOutOfStopPriceRange,
        'order_unplaceable_maker_only': OrderUnplaceableMakerOnly,
        'order_unplaceable_taker_only': OrderUnPlaceableTakerOnly,
        'order_exceeded_asset_values': OrderExceededAssetValues,
        'order_already_closed': OrderAlreadyClosed,

        # Wdrl
        'wdrl_invalid_coin': WdrlInvalidCoin,
        'wdrl_suspended_coin': WdrlSuspendedCoin,
        'wdrl_precision_error': WdrlPrecisionError,
        'wdrl_under_min_amount': WdrlUnderMinAmount,
        'wdrl_over_daily_wdrl_limit': WdrlOverDailyWdrlLimit,
        'wdrl_exceeded_asset_values': WdrlExceededAssetValues,
        'wdrl_needs_to_tag': WdrlNeedsToTag,
        'wdrl_needs_to_org': WdrlNeedsToOrg,
        'wdrl_invalid_addr': WdrlInvalidAddr,
    }

    return switcher.get(code, ResponseError)
