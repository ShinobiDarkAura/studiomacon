"""Built-in copy for the content pages.

Used until a page is edited in the admin — once store_pages.body has blocks,
build.py renders those instead. Keeps the site correct before the editor exists.
"""

FALLBACK = {
    "story": {
        "file": "story.html",
        "title": "Our Story",
        "page_title": "Studio Maçon ⚚ Our Story",
        "desc": "The story of Studio Maçon — Alex and Hannah, sculptural jewelry cast by hand in California.",
        "html": '''    <h3>Our Practice</h3>
    <p class="lead">Each piece begins as a sketch on paper. Next, the object is carved by hand &mdash; first in wax, then fine-tuned in metal. We work closely with a local foundry to cast the wax carvings in bronze, silver or gold. Each piece is then refined and polished in our studio.</p>
    <p>If its path is to become a collection piece, a rubber mold is made so that we can make the children of that original and share them with you. If it's a custom piece, it is one of a kind.</p>
    <div class="steps">
      <figure><img src="images/content/draw.png" alt="Concept &amp; sketch"><figcaption>Concept &amp; Sketch</figcaption></figure>
      <figure><img src="images/content/cast.png" alt="Carve &amp; cast"><figcaption>Carve &amp; Cast</figcaption></figure>
      <figure><img src="images/content/polish.png" alt="Polish &amp; patina"><figcaption>Polish &amp; Patina</figcaption></figure>
    </div>
    <h3>Our History</h3>
    <p>Maçon is based in southern California, but Alex and Hannah met at RISD in 2008. They had figure drawing class together freshman year and quickly became close friends.</p>
    <p>After graduating college, their resilient love for each other &mdash; despite gaps in distance and time &mdash; never waned. Eventually they found their way back to each other and married in 2023. Both Maçon and their union were born out of their desire to live and create as one.</p>
    <div class="twoup"><img src="images/content/hannah.png" alt="Hannah as a child"><img src="images/content/alex.png" alt="Alex as a child"></div>
    <p class="lead">We discover by holding.</p>
    <p>Maçon was founded by two creative and life partners, Alex and Hannah. Their work is inspired by ancient artifacts and the intimate and personal objects they cared for when they were children.</p>
    <img src="images/content/hand-milo.png" alt="Hand holding Milo">''',
    },
    "custom": {
        "file": "custom.html",
        "title": "Custom Heirlooms",
        "page_title": "Maçon ⚚ Custom Heirlooms",
        "desc": "Commission a custom heirloom from Studio Maçon.",
        "html": '''    <p class="lead">Let's make something real together.</p>
    <p>It's a rare privilege to create custom heirlooms to honor a special moment. If you're interested in commissioning a piece for yourself or someone you love, <a href="contact.html">reach out to us here</a>.</p>
    <img src="images/content/lorenz.jpg" alt="Lorenz Ring, 2023">
    <p style="text-align:center;color:var(--olive);font-size:13px;letter-spacing:.06em">Lorenz Ring, 2023</p>
    <div class="twoup"><img src="images/content/custom-2.jpg" alt="Custom work"><img src="images/content/custom-3.jpg" alt="Custom work"></div>''',
    },
    "shipping": {
        "file": "shipping.html",
        "title": "Shipping & Returns",
        "page_title": "Maçon ⚚ Shipping & Returns",
        "desc": "Shipping and returns policy for Studio Maçon.",
        "html": '''    <h3>Shipping</h3>
    <p>Each piece is individually made to order; please allow up to 10 business days for us to create your piece before it heads out to you.</p>
    <p>Standard shipping takes 3&ndash;7 business days for delivery, while international shipping generally takes 5&ndash;10 business days depending on shipping destination.</p>
    <h3>Returns</h3>
    <p>We will accept pieces (excluding custom work) in their original condition for store credit towards your next purchase. For pieces that don't fit properly, we will gladly work with you to find the right size. Returns and exchanges must be initiated within 14 days of the delivery date.</p>
    <p><a href="mailto:hello@studiomacon.co?subject=Hi!%20I%27d%20like%20to%20start%20a%20return.">Contact us</a> to initiate a return. Include your order number and please let us know the reason for your return. After your return has been successfully processed, you will receive store credit and a confirmation email.</p>
    <img src="images/content/olive-branch.png" alt="Olive branch" style="max-width:340px">''',
    },
    "contact": {
        "file": "contact.html",
        "title": "Contact",
        "page_title": "Maçon ⚚ Contact",
        "desc": "Get in touch with Studio Maçon.",
        "wrap_class": "contact",
        "pre": '    <img class="leaves" src="images/content/leaves.png" alt="">',
        "html": '''    <p style="text-align:center"><a href="https://www.instagram.com/studiomacon/">@studiomacon</a> &nbsp;&middot;&nbsp; <a href="mailto:hello@studiomacon.co?subject=Hi%20there!">hello@studiomacon.co</a></p>
    <form id="cform" class="cform">
      <div class="row2"><input name="first" placeholder="First Name" required><input name="last" placeholder="Last Name"></div>
      <input name="email" type="email" placeholder="Email" required>
      <textarea name="message" rows="5" placeholder="Message" required></textarea>
      <button type="submit">Send</button>
    </form>''',
    },
}
