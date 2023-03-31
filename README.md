## Meta-genome Flask API

This api communicates the react front page with portal.meta-genome.org via pycdcs

By default pycdcs provides a pandas dataframe of submissions metadata and xml content. This xml content is then parsed according to the requests from the front page. Data is then compiled and organised into a json object and returned to the front page.

xml_parse_api.py contains the necessary xml parsing functions