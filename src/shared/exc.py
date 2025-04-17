class SetupError(Exception):

    def __init__(
        self,
        msg="Submission failed due to an internal error - please contact administrator"
    ):
        super().__init__(msg)


class SubmissionError(Exception):

    def __init__(
        self,
        msg="Submission of job failed - this may be caused by an invalid configuration or an internal error"
    ):
        super().__init__(msg)


class ProcessingError(Exception):

    def __init__(
        self,
        msg="Processing of benchmark results failed due to an internal error - please contact administrator"
    ):
        super().__init__(msg)
