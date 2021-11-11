
#!python3
# Author: Uğur Erdem Seyfi
# A socket program that downloads data from the urls in a given index, using HTTP
import socket  # for socket
import sys  # for system
import re  # for regex

DEFAULT_RECEIVE = 8192
HTTP_PORT = 80  # for http


def main(argv):
    argv_len = len(argv)
    if(argv_len == 0):
        return False  # throw an error
    index_url = argv[0]

    bound_entered = (argv_len > 1)
    lower_endpoint, upper_endpoint = map(int, argv[1].split(
        '-')) if bound_entered else (1, 100000)

    print("URL of the index file: {}".format(index_url))
    print("Lower endpoint: {} \r\nUpper endpoint: {}".format(
        lower_endpoint, upper_endpoint) if bound_entered else "No range is given")
    response, _ = http_request_get(index_url, DEFAULT_RECEIVE)

    if('200' not in response['status']):
        raise Exception('Requested file is not found')
        sys.close()

    data = response['data']
    urls = extract_urls(data)

    print("Index file is downloaded")
    print("There are {} files in the index".format(len(urls)))

    # list the files
    count = 1
    for url in urls:
        download_status = process_download(
            url, lower_endpoint, upper_endpoint, bound_entered)
        print("{}. {} {}".format(count, url, download_status))
        count = count + 1


def process_download(url, lower_endpoint, upper_endpoint, bound_entered=False):
    _res, head_len = http_request_head(
        url)
    # check status
    if('404' in _res['status']):
        return "is not found"
    else:
        content_length = int(_res['Content-Length'])
        if(bound_entered and content_length <= lower_endpoint):
            return "(size= {}) is not downloaded".format(content_length)
        # if file found,decide whether its downloaded or not
        _res, _ = http_request_get(url, content_length, head_len)
        file_name = url.split('/').pop()
        with open(file_name, 'a') as f:
            f.write(
                _res['data'][lower_endpoint:upper_endpoint if not bound_entered else content_length])
            f.close()
        if not bound_entered:
            return "(size = {}) is downloaded".format(content_length)
        return "(range = {}-{}) is downloaded".format(lower_endpoint, upper_endpoint if content_length > upper_endpoint + lower_endpoint else content_length)


def extract_urls(data):
    urls = []
    url_pattern = re.compile(
        "((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*")

    for url in data.split('\\n'):
        if url_pattern.match(url):
            urls.append(url)
    return urls


def http_request_head(url):
    target_host, target_endpoint = url_to_target(url)
    request = "HEAD {0} HTTP/1.1\r\nHost:{1}\r\n\r\n".format(
        target_endpoint, target_host)
    return http_request(target_host, request, DEFAULT_RECEIVE)


def http_request_get(url, content_length, head_len=DEFAULT_RECEIVE):
    target_host, target_endpoint = url_to_target(url)
    # send some data
    request = "GET {0} HTTP/1.1\r\nHost:{1}\r\n\r\n".format(
        target_endpoint, target_host)
    return http_request(target_host, request, content_length + head_len)

# method for http queries


def url_to_target(url):
    target_host = url.split("/")[0]
    tmp = url.replace(target_host, "")
    target_endpoint = tmp if tmp != "" else "/"
    return target_host, target_endpoint


def http_request(target_host, request, recv_len):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # socket object

    # connect the client
    client.connect((target_host, HTTP_PORT))

    # send some data
    client.send(request.encode())

    # receive some data
    response = client.recv(recv_len)
    http_response = repr(response)
    http_response_len = len(http_response)

    client.close()
    return parse_http(http_response), http_response_len

# method for parsing the http response


def parse_http(http):
    fields = http.split("\\r\\n")
    output = {}
    output['status'] = fields[0]
    for field in fields[1:]:
        if not ':' in field:
            continue
        key, value = field.split(':', 1)
        output[key] = value
    output['data'] = fields[len(fields) - 1]
    return output


if __name__ == "__main__":
    main(sys.argv[1:])
