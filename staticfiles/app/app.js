'use strict';
//htmx.logAll();
// Close offcanvas nav after selection
function hideNavBar() {
    const bsOffcanvas = bootstrap.Offcanvas.getInstance('#offcanvasNavbar');
    bsOffcanvas.hide();
};
