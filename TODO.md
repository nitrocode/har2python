1. [DONE] - Read har
2. Find patterns (hardest part...)
    - [DONE] check url by splitting by forward slash and searching for values
    - [DONE] recursively iterate through postData
    - [DONE] recursively iterate through queryString
    - recursively iterate through response

    Example dictionary:

        variable_values = {
            'aaaaaaaaaaaaaaaaaaguid': {
                'count': 5
                'locations': [
                    # request num index can be used to find the original request
                    #   which will contain the method, url, etc
                    # in json response -- note: resp=true
                    {
                        'index': 3,
                        'loc': 'data.object.project_guid'
                    },
                    # fed into query
                    {
                        'index': 6,
                        'loc': '...'
                    }
                    ...
                ]
            },
            'someotherguidaaaaaaaaaa': {...},
        }

3. Recreate har

    1. Go through each variable with count > 1
    2. Replace each value in har with a variable name

4. Convert har to python code
    - May need to be modified...
5. [LOW PRIORITY] - Convert har to documentation (separate script)
    each request...
    - shows headers
    - shows curl statement
    - shows method
    - shows parameters
    - shows response
