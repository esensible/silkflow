from . import html


def js_code(callback_url, poll_url, initial_state):
    return f"""
        state = {initial_state};

        replaceKey = function (key, index, newHtml) {{
            var parent = document.querySelector('[key="' + key + '"]');
            if (!parent) {{ return; }}
            var child = parent.childNodes[index];
            if (!child) {{ return; }}
            var tempContainer = document.createElement('div');
            tempContainer.innerHTML = newHtml;
            var newElement = tempContainer.firstChild;
            parent.replaceChild(newElement, child);
        }};
        pythonImpl = function (id, event) {{
            var xhr = new XMLHttpRequest();
            xhr.open('POST', "{callback_url}", true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.onreadystatechange = function() {{
                if (xhr.readyState === 4 && xhr.status === 200) {{
                    var redirectUrl = xhr.getResponseHeader("X-Redirect-URL");
                    if (redirectUrl) {{
                        window.location.href = redirectUrl;
                    }} else {{
                        var data = JSON.parse(xhr.responseText);
                        if (data) {{
                            // TODO: update timestamp offset here
                        }}
                    }}
                }}
            }};
            xhr.send(JSON.stringify({{
                id: id,
                event: {{test: 23}}
            }}));
        }};
        python = function(id) {{
            return function (e) {{
                pythonImpl(id, e);
                return false;
            }};
        }};
        confirm = function(id, count) {{
            if (typeof count === 'undefined') {{
                count = 0;
            }}

            return function (e) {{
                confirmImpl(id, e, count);
                return false;
            }}
        }};

        confirmImpl = (function(size, screenWidth, screenHeight, timeout) {{
            var existingButton;

            return function(id, e, count) {{
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
                        confirmImpl(id, e, count - 1);
                    }} else {{
                        pythonImpl(id, e);
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

        (function() {{
            var apply_ms;

            function pollServer() {{
                var xhr = new XMLHttpRequest();
                var url = "{poll_url}?state=" + state;
                if (typeof apply_ms !== 'undefined') {{
                    url += "&apply_ms=" + apply_ms;
                }}
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
                                var applyStartTime = new Date().getTime();
                                var data = JSON.parse(xhr.responseText);
                                if (data) {{
                                    state = data.state;
                                    data.updates.forEach(function(item) {{
                                        replaceKey(item[0], item[1], item[2]);
                                    }});
                                    apply_ms = new Date().getTime() - applyStartTime;
                                }} else {{
                                    apply_ms = undefined;
                                }}
                            }}
                        }}
                        setTimeout(pollServer, 0);
                    }}
                }};
                xhr.send();
            }}

            pollServer();
        }})();        
    """


def render(body, callback_url, poll_url, initial_state, head_elems=[]):
    return html.html(
        html.head(
            html.script(js_code(callback_url, poll_url, initial_state)), *head_elems
        ),
        *body,
    )
