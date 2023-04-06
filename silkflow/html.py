from .core import _factory

# Content sectioning
address = _factory("address")
article = _factory("article")
aside = _factory("aside")
footer = _factory("footer")
h1 = _factory("h1")
h2 = _factory("h2")
h3 = _factory("h3")
h4 = _factory("h4")
h5 = _factory("h5")
h6 = _factory("h6")
header = _factory("header")
hgroup = _factory("hgroup")
nav = _factory("nav")
section = _factory("section")

# Text content
blockquote = _factory("blockquote")
dd = _factory("dd")
div = _factory("div")
dl = _factory("dl")
dt = _factory("dt")
figcaption = _factory("figcaption")
figure = _factory("figure")
hr = _factory("hr", allow_children=False)
li = _factory("li")
ol = _factory("ol")
p = _factory("p")
pre = _factory("pre")
ul = _factory("ul")

# Inline text semantics
a = _factory("a")
abbr = _factory("abbr")
b = _factory("b")
br = _factory("br", allow_children=False)
cite = _factory("cite")
code = _factory("code")
data = _factory("data")
em = _factory("em")
i = _factory("i")
kbd = _factory("kbd")
mark = _factory("mark")
q = _factory("q")
s = _factory("s")
samp = _factory("samp")
small = _factory("small")
span = _factory("span")
strong = _factory("strong")
sub = _factory("sub")
sup = _factory("sup")
time = _factory("time")
u = _factory("u")
var = _factory("var")

# Image and video
img = _factory("img", allow_children=False)
audio = _factory("audio")
video = _factory("video")
source = _factory("source", allow_children=False)

# Table content
caption = _factory("caption")
col = _factory("col")
colgroup = _factory("colgroup")
table = _factory("table")
tbody = _factory("tbody")
td = _factory("td")
tfoot = _factory("tfoot")
th = _factory("th")
thead = _factory("thead")
tr = _factory("tr")

# Forms (only read only aspects)
meter = _factory("meter")
output = _factory("output")
progress = _factory("progress")
input_ = _factory("input", allow_children=False)
button = _factory("button")
label = _factory("label")

# Interactive elements
details = _factory("details")
dialog = _factory("dialog")
menu = _factory("menu")
menuitem = _factory("menuitem")
summary = _factory("summary")

style = _factory("style")

# # Non-standard for reactive hooks
# string = String
# attr = Attribute
