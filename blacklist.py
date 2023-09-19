class BlackList:
    """A class holding methods to determine if a company is blacklisted"""

    BLACKLISTED_COMPANIES = set(
        ["Pattern Learning AI - Career & Tech Recruitment Reimagined!"]
    )

    def is_blacklisted_company(self, company: str) -> bool:
        """Determines if the company is blacklisted or not"""

        return True if company in self.BLACKLISTED_COMPANIES else False
