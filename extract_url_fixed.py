# Function to extract URL from Archive Testcase field
def extract_url(archive_testcase):
    if not archive_testcase:
        return ""
    
    # Match the URL pattern inside parentheses
    url_match = re.search(r'\((https?://[^\s)]+)\)', archive_testcase)
    if url_match:
        return url_match.group(1)
    return ""
