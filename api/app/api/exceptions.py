class InsufficientCreditsError(Exception):
    def __init__(self, available_credits: int, required_tokens: int):
        self.status_code = 429
        self.message = (
            f'Insufficient credits to process this request. '
            f'You currently have {available_credits} credits available, but this operation requires {required_tokens} credits. '
            f'Either upgrade your subscription tier, or wait for your credits to be replenished.'
        )
        super().__init__(self.message)

class NoProviderAvailableError(Exception):
    def __init__(self):
        self.status_code = 503
        self.message = (
            'The requested model is temporarily unavailable due to no active providers. '
            'This is likely a temporary issue. Please try again in a few minutes, '
            'or select a different model.'
        )
        super().__init__(self.message)