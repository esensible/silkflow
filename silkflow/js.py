from . import html

def console_log(url):
    return f"""
        (function() {{
        var originalConsoleLog = console.log;
        var endpointUrl = '{url}';

        function sendLogToServer(message) {{
            var xhr = new XMLHttpRequest();
            xhr.open('POST', endpointUrl, true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.send(JSON.stringify({{ log: message }}));
        }}

        console.log = function() {{
            var args = Array.prototype.slice.call(arguments);
            var message = args.join(' ');

            originalConsoleLog.apply(console, args);
            sendLogToServer(message);
        }};

        window.onerror = function(message, source, lineno, colno, error) {{
            var errorDetails = {{
            message: message,
            source: source,
            lineno: lineno,
            colno: colno,
            error: error ? error.stack : null
            }};

            sendLogToServer(JSON.stringify(errorDetails));
        }};
        }})();
    """


def offset_manager(window_len):
    return f"""
        (function (maxListSize) {{
            var offsets = [];

            function addTime(serverTime) {{
                var clientTime = new Date().getTime();
                var offset = serverTime - clientTime;

                if (offsets.length >= maxListSize) {{
                    offsets.shift();
                }}
                offsets.push(offset);
            }}

            function getOffsetTime() {{
                var now = new Date().getTime();
                var averageOffset = offsets.reduce(function (a, b) {{ return a + b; }}, 0) / offsets.length;
                return now + averageOffset;
            }}

            return {{
                addTime: addTime,
                getOffsetTime: getOffsetTime
            }};
        }})({window_len});
    """


def polling_loop(poll_url, initial_state, time_manager):
    return f"""
        (function(timeOffsetManager, initial_state, poll_url) {{
            var state = {initial_state};
            var tempContainer = document.createElement('div');

            var replaceKey = function (key, index, newHtml) {{
                var parent = document.querySelector('[key="' + key + '"]');
                if (!parent) {{ return; }}               
                if (typeof index === 'string') {{
                    parent.setAttribute(index, newHtml);
                }} else {{
                    var child = parent.childNodes[index];
                    if (!child) {{ return; }}
                    tempContainer.innerHTML = newHtml;
                    var newElement = tempContainer.firstChild;
                    parent.replaceChild(newElement, child);
                }}
            }};

            function pollServer() {{
                var xhr = new XMLHttpRequest();
                var url = "{poll_url}?state=" + state;
                xhr.open('GET', url, true);
                xhr.setRequestHeader('Content-Type', 'application/json');
                xhr.setRequestHeader('Cache-Control', 'no-cache, no-store, must-revalidate');
                xhr.setRequestHeader('Pragma', 'no-cache');
                xhr.setRequestHeader('Expires', '0');
                xhr.onreadystatechange = function() {{
                    if (xhr.readyState === 4) {{
                        if (xhr.status === 200) {{
                            var redirectUrl = xhr.getResponseHeader("X-Redirect-URL");
                            if (redirectUrl) {{
                                window.location.href = redirectUrl;
                            }} else {{
                                var data = JSON.parse(xhr.responseText);
                                if (data) {{
                                    state = data.state;
                                    data.updates.forEach(function(item) {{
                                        replaceKey(item[0], item[1], item[2]);
                                    }});
                                    if (data.time !== undefined) {{
                                        timeOffsetManager.addTime(data.time);
                                    }}
                                }}
                            }}
                        }}
                        setTimeout(pollServer, 0);
                    }}
                }};
                xhr.send();
            }}

            pollServer();
        }})({time_manager})
    """


def callback_handlers(callback_url, offset_manager):
    return f"""
        pythonImpl = function (id, event, timestamp) {{
            var xhr = new XMLHttpRequest();
            xhr.open('POST', "{callback_url}", true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.onreadystatechange = function() {{
                if (xhr.readyState === 4 && xhr.status === 200) {{
                    var redirectUrl = xhr.getResponseHeader("X-Redirect-URL");
                    if (redirectUrl) {{
                        window.location.href = redirectUrl;
                    }}
                }}
            }};
            xhr.send(JSON.stringify({{
                id: id,
                event: {{time: timestamp}},
            }}));
        }};

        python = function(id) {{
            return function (e) {{
                var timestamp = {offset_manager}.getOffsetTime();
                pythonImpl(id, e, timestamp);
                return false;
            }};
        }};

        confirm = function(id, count) {{
            if (typeof count === 'undefined') {{
                count = 0;
            }}

            return function (e) {{
                var timestamp = {offset_manager}.getOffsetTime();
                confirmImpl(id, e, count, timestamp);
                return false;
            }}
        }};

        confirmImpl = (function(size, screenWidth, screenHeight, timeout) {{
            var existingButton;

            return function(id, e, count, timestamp) {{
                if (existingButton) {{
                    existingButton.parentNode.removeChild(existingButton);
                }}

                var leftPosition = Math.random() * (screenWidth - 2 * size) + size;
                var topPosition = Math.random() * (screenHeight - 2 * size) + size;

                var floatingButton = document.createElement('button');

                floatingButton.style.position = 'absolute';
                floatingButton.style.left = leftPosition + 'px';
                floatingButton.style.top = topPosition + 'px';
                floatingButton.style.width = size + 'px';
                floatingButton.style.height = size + 'px';
                floatingButton.className = 'confirm';

                floatingButton.onclick = function() {{
                    clearTimeout(removeTimeout);
                    floatingButton.parentNode.removeChild(floatingButton);
                    existingButton = null;

                    if (count > 1) {{
                        confirmImpl(id, e, count - 1, timestamp);
                    }} else {{
                        pythonImpl(id, e, timestamp);
                    }}
                    return false;
                }};

                document.body.appendChild(floatingButton);

                var removeTimeout = setTimeout(function() {{
                    floatingButton.parentNode.removeChild(floatingButton);
                    existingButton = null;
                }}, timeout);

                existingButton = floatingButton;

            }};
        }})(100, 1272, 1474 - 500, 5000);     
    """


def js_script(callback_url, poll_url, log_url, initial_state):
    return html.script(
        f"""
        var offsetManager = {offset_manager(5)};

        {polling_loop(poll_url, initial_state, "offsetManager")}

        {callback_handlers(callback_url, "offsetManager")};

        {console_log(log_url)};
    """
    )


def render(body, callback_url, poll_url, log_url, initial_state, head_elems=[]):
    return html.html(
        html.head(
            js_script(callback_url, poll_url, log_url, initial_state),
            *head_elems,
        ),
        *body,
    )
