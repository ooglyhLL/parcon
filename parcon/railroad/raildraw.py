
"""
This module provides support for drawing railroad diagrams created by
parcon.railroad (which usually creates them from Parcon parsers) into image
files or other locations.

It's possible to use this module and parcon.railroad as standalone modules to
create syntax diagrams for things unrelated to Parcon. I'll write up
documentation on how to use this module separate from Parcon at some point.

A simple example of how to use this module is present in the module
documentation of parcon.railroad.

This module requires Cairo and PyCairo in order to function. These must be
installed separately from Parcon; both Cairo and PyCairo are available for
Windows, Linux, and Mac. A Google search should turn up information on where to
download and install both. (If it doesn't, go to pypi.python.org/pypi/parcon
and send an email to the email address you find there.)

This module also requires Pango and PyGTK (for the Pango bindings). A similar
Google search should turn up information on how to install these.

If you're on Ubuntu, all of the above dependencies can be installed via
apt-get; I'll get a list of the specific packages to install up here soon.
"""

from __future__ import division, print_function
from operator import itemgetter
from parcon import railroad as rr
from parcon import options
from math import radians
try:
    import cairo
    import gi
    gi.require_foreign('cairo')
    gi.require_version('Pango', '1.0')
    gi.require_version('PangoCairo', '1.0')
    from gi.repository import Pango, PangoCairo
except ImportError:
    print("ERROR: parcon.railroad.raildraw requires Cairo, PyCairo, Pango,"
          "and PyGTK (for the Pango bindings). Please install any of those "
          "that you may be missing. An ImportError is about to be raised as "
          "a result of one of those not being present.")
    raise


# We have two dicts, one that maps railroad classes (Then, Or, Token, etc.) to
# functions that return (width, height, line_position) and one that maps
# railroad classes to functions that draw them.

size_functions = {}
draw_functions = {}

plain_font = Pango.FontDescription("sans 10")
bold_font = Pango.FontDescription("sans bold 10")
italic_font = Pango.FontDescription("sans italic 10")
bold_italic_font = Pango.FontDescription("sans bold italic 10")
title_font = Pango.FontDescription("sans bold 14")
default_line_size = 2

def create_options(map):
    return options.Options(map,
        raildraw_production_font=plain_font,
        raildraw_text_font=bold_font,
        raildraw_anycase_font=plain_font,
        raildraw_description_font=italic_font,
        raildraw_title_font=title_font,
        raildraw_title_before=45,
        raildraw_title_after=45,
        raildraw_title_hide=False,
        raildraw_arrow_width=9,
        raildraw_arrow_height=7,
        raildraw_arrow_indent=0.25,
        raildraw_size_of_arrow=size_of_arrow,
        raildraw_draw_arrow=draw_arrow,
        raildraw_token_padding=1,
        raildraw_token_margin=0,
        raildraw_token_rect_padding=12,
        raildraw_then_before_arrow=8,
        raildraw_then_after_arrow=0,
        raildraw_line_size=1.6,
        raildraw_or_spacing=8,
        raildraw_or_radius=7,
        raildraw_or_before=0,
        raildraw_or_after=4,
        raildraw_bullet_radius=2.5,
        raildraw_loop_spacing=8,
        raildraw_loop_radius=7,
        raildraw_loop_before=6,
        raildraw_loop_after=6,
        raildraw_scale=1.0
    )


def f(map, key):
    """
    A function decorator that results in the specified function being added
    to the specified map under the specified key.
    """
    def decorator(function):
        map[key] = function
        return function
    return decorator


def size_of(context, construct, options):
    return size_functions[type(construct)](context, construct, options)


def draw(context, x, y, construct, options, forward):
    return draw_functions[type(construct)](context, x, y, construct, options, forward)


def get_font_for_token(options, token):
    if token.type == rr.PRODUCTION:
        return options.raildraw_production_font
    if token.type == rr.TEXT:
        return options.raildraw_text_font
    if token.type == rr.ANYCASE:
        return options.raildraw_anycase_font
    if token.type == rr.DESCRIPTION:
        return options.raildraw_description_font
    raise ValueError


def draw_arrow(context, x, y, options, forward):
    """
    Draws an arrow at the specified position.
    """
    width, height = size_of_arrow(options)
    line_pos = height / 2
    indent = options.raildraw_arrow_indent * width
    if forward:
        context.move_to(x, y + line_pos)
        context.line_to(x + indent, y + line_pos)
        context.stroke()
        context.move_to(x, y)
        context.line_to(x + width, y + line_pos)
        context.line_to(x, y + height)
        context.line_to(x + indent, y + line_pos)
    else:
        context.move_to(x + width, y + line_pos)
        context.line_to(x + (width - indent), y + line_pos)
        context.stroke()
        context.move_to(x + width, y)
        context.line_to(x, y + line_pos)
        context.line_to(x + width, y + height)
        context.line_to(x + (width - indent), y + line_pos)
    context.close_path()
    context.fill()


def draw_line(context, x1, y1, x2, y2):
    if x1 == y1 and x2 == y2: # Empty line
        return
    context.move_to(x1, y1)
    context.line_to(x2, y2)
    context.stroke()


def size_of_arrow(options):
    """
    Returns the size of an arrow, in the same format as all of the other size
    functions, namely (width, height, line_position).
    """
    width = options.raildraw_arrow_width
    height = options.raildraw_arrow_height
    return width, height


@f(size_functions, rr.Nothing)
def size_of_Nothing(context, construct, options):
    width, height = options.raildraw_size_of_arrow(options)
    return width, height, height / 2


@f(draw_functions, rr.Nothing)
def draw_Nothing(context, x, y, construct, options, forward):
    return options.raildraw_draw_arrow(context, x, y, options, forward)


@f(size_functions, rr.Token)
def size_of_Token(context, construct, options):
    layout = PangoCairo.create_layout(context)
    layout.set_text(construct.text, -1)
    layout.set_font_description(get_font_for_token(options, construct))
    text_width, text_height = layout.get_pixel_size()
    h_padding = options.raildraw_token_padding
    v_padding = options.raildraw_token_padding
    if construct.type not in (rr.TEXT, rr.ANYCASE):
        h_padding += options.raildraw_token_rect_padding
    margin = options.raildraw_token_margin
    height = text_height + (v_padding * 2) + (margin * 2)
    width = text_width + (h_padding * 2) + (margin * 2)
    if construct.type in (rr.TEXT, rr.ANYCASE):
        # TEXT and ANYCASE are drawn with half-circles on either end, so we
        # need to account for the size of these circles. What we add here is
        # the diameter of these circles, which accounts for a half circle at
        # either end.
        width += text_height + (v_padding * 2)
    return (width, height, height / 2)


@f(draw_functions, rr.Token)
def draw_Token(context, x, y, construct, options, forward):
    margin = options.raildraw_token_margin
    h_padding = options.raildraw_token_padding
    v_padding = options.raildraw_token_padding
    if construct.type not in (rr.TEXT, rr.ANYCASE):
        h_padding += options.raildraw_token_rect_padding
    layout = PangoCairo.create_layout(context)
    layout.set_text(construct.text, -1)
    layout.set_font_description(get_font_for_token(options, construct))
    text_width, text_height = layout.get_pixel_size()
    if construct.type in (rr.TEXT, rr.ANYCASE):
        diameter = v_padding + text_height + v_padding
        radius = diameter / 2
        context.move_to(x + margin + radius + h_padding, y + margin + v_padding)
        PangoCairo.show_layout(context, layout)
        context.move_to(x + margin + radius, y + margin)
        context.line_to(x + margin + radius + h_padding + text_width + h_padding, y + margin)
        context.arc(x + margin + radius + h_padding + text_width + h_padding, y + margin + radius, radius, radians(270), radians(90))
        context.line_to(x + margin + radius, y + margin + v_padding + text_height + v_padding)
        context.arc(x + margin + radius, y + margin + radius, radius, radians(90), radians(270))
        context.close_path() # Shouldn't have any effect since we're already at
        # the start, but just in case
        context.stroke()
        width = margin + radius + h_padding + text_width + h_padding + radius + margin
    else:
        context.move_to(x + margin + h_padding, y + margin + v_padding)
        PangoCairo.show_layout(context, layout)
        context.move_to(x + margin, y + margin)
        context.line_to(x + margin + h_padding + text_width + h_padding, y + margin)
        context.line_to(x + margin + h_padding + text_width + h_padding, y + margin + v_padding + text_height + v_padding)
        context.line_to(x + margin, y + margin + v_padding + text_height + v_padding)
        context.close_path()
        context.stroke()
        width = margin + h_padding + text_width + h_padding + margin
    context.move_to(x, y + margin + v_padding + (text_height / 2))
    context.line_to(x + margin, y + margin + v_padding + (text_height / 2))
    context.stroke()
    context.move_to(x + width, y + margin + v_padding + (text_height / 2))
    context.line_to(x + width - margin, y + margin + v_padding + (text_height / 2))
    context.stroke()


@f(size_functions, rr.Then)
def size_of_Then(context, construct, options):
    constructs = construct.constructs
    sizes = [size_of(context, c, options) for c in constructs]
    before_heights = [l for w, h, l in sizes]
    after_heights = [h - l for w, h, l in sizes]
    max_before = max(before_heights)
    max_after = max(after_heights)
    arrow_line_size = (options.raildraw_then_before_arrow + 
                       options.raildraw_size_of_arrow(options)[0] + 
                       options.raildraw_then_after_arrow)
    return sum([w for w, h, l in sizes]) + (len(sizes) - 1) * arrow_line_size, max_before + max_after, max_before


@f(draw_functions, rr.Then)
def draw_Then(context, x, y, construct, options, forward):
    constructs = construct.constructs
    arrow_before = options.raildraw_then_before_arrow
    arrow_after = options.raildraw_then_after_arrow
    if not forward:
        constructs = list(reversed(constructs))
        arrow_before, arrow_after = arrow_after, arrow_before
    arrow_width, arrow_height = options.raildraw_size_of_arrow(options)
    width, height, line_position = size_of_Then(context, construct, options)
    current_x = x
    for index, c in enumerate(constructs):
        c_width, c_height, c_line_position = size_of(context, c, options)
        draw(context, current_x, y + (line_position - c_line_position), c, options, forward)
        current_x += c_width
        if index != (len(constructs) - 1):
            draw_line(context, current_x, y + line_position, current_x + arrow_before, y + line_position)
            current_x += arrow_before
            options.raildraw_draw_arrow(context, current_x, y + line_position - (arrow_height / 2), options, forward)
            current_x += arrow_width
            draw_line(context, current_x, y + line_position, current_x + arrow_after, y + line_position)
            current_x += arrow_after


@f(size_functions, rr.Or)
def size_of_Or(context, construct, options):
    constructs = construct.constructs
    if len(constructs) == 1:
        return size_of(context, constructs[0], options)
    sizes = [size_of(context, c, options) for c in constructs]
    max_width = max(sizes, key=itemgetter(0))[0]
    total_height = sum([h for w, h, l in sizes])
    arrow_width, arrow_height = options.raildraw_size_of_arrow(options)
    width = ((options.raildraw_or_radius * 4) + options.raildraw_or_before
             + max_width + options.raildraw_or_after + (arrow_width * 2))
    height = total_height + ((len(constructs) - 1) * options.raildraw_or_spacing)
    # Line position of Or is the line position of its first construct
    return width, height, sizes[0][2]


@f(draw_functions, rr.Or)
def draw_Or(context, x, y, construct, options, forward):
    if len(construct.constructs) == 1:
        return draw(context, x, y, construct.constructs[0], options, forward)
    width, height, line_position = size_of_Or(context, construct, options)
    constructs = construct.constructs
    sizes = [size_of(context, c, options) for c in constructs]
    max_width = max(sizes, key=itemgetter(0))[0]
    radius = options.raildraw_or_radius
    spacing = options.raildraw_or_spacing
    arrow_width, arrow_height = options.raildraw_size_of_arrow(options)
    before = options.raildraw_or_before
    after = options.raildraw_or_after
    if not forward:
        before, after = after, before
    current_y = y
    for index, (c, (w, h, l)) in enumerate(zip(constructs, sizes)):
        draw_arrows = not isinstance(c, rr.Nothing)
        # Don't draw arrows if c is a loop and its component is not Nothing;
        # the arrows tend to appear superfluous in such a case
        if isinstance(c, rr.Loop) and not isinstance(c.component, rr.Nothing):
            draw_arrows = False
        if index != 0:
            context.move_to(x + radius, current_y + l - radius)
            context.arc_negative(x + radius * 2, current_y + l - radius, radius, radians(180), radians(90))
            context.stroke()
        if not draw_arrows:
            draw_line(context, x + radius * 2, current_y + l, x + radius * 2 + arrow_width, current_y + l)
        else:
            options.raildraw_draw_arrow(context, x + radius * 2, current_y + l - (arrow_height / 2), options, forward)
        draw_line(context, x + radius * 2 + arrow_width, current_y + l, x + radius * 2 + arrow_width + before, current_y + l)
        construct_x = x + radius * 2 + arrow_width + before
        if isinstance(c, rr.Nothing):
            draw_line(context, construct_x, current_y + l, construct_x + max_width / 2 - w / 2, current_y + l)
            draw(context, construct_x + max_width / 2 - w / 2, current_y, c, options, forward)
            draw_line(context, construct_x + max_width / 2 + w / 2, current_y + l, construct_x + max_width + after, current_y + l)
        else:
            draw(context, construct_x, current_y, c, options, forward)
            draw_line(context, construct_x + w, current_y + l, construct_x + max_width + after, current_y + l)
        if not draw_arrows:
            draw_line(context, construct_x + max_width + after, current_y + l, construct_x + max_width + after + arrow_width, current_y + l)
        else:
            options.raildraw_draw_arrow(context, construct_x + max_width + after, current_y + l - (arrow_height / 2), options, forward)
        if index != 0:
            context.move_to(construct_x + max_width + after + arrow_width, current_y + l)
            context.arc_negative(construct_x + max_width + after + arrow_width, current_y + l - radius, radius, radians(90), radians(0))
            context.stroke()
        if index == len(constructs) - 1: # Last construct
            line_end_y = current_y + l - radius
        current_y += spacing + h
    context.move_to(x, y + line_position)
    context.arc(x, y + line_position + radius, radius, radians(270), radians(0))
    context.line_to(x + radius, line_end_y)
    context.stroke()
    draw_line(context, x, y + line_position, x + radius * 2, y + line_position)
    end_x = x + radius * 2 + arrow_width + before + max_width + after + arrow_width 
    draw_line(context, end_x, y + line_position, end_x + radius * 2, y + line_position)
    context.move_to(x + width, y + line_position)
    context.arc_negative(x + width, y + line_position + radius, radius, radians(270), radians(180))
    context.line_to(x + width - radius, line_end_y)
    context.stroke()


@f(size_functions, rr.Loop)
def size_of_Loop(context, construct, options):
    component = construct.component
    delimiter = construct.delimiter
    c_width, c_height, c_line_pos = size_of(context, component, options)
    d_width, d_height, d_line_pos = size_of(context, delimiter, options)
    radius = options.raildraw_loop_radius
    before = options.raildraw_loop_before
    after = options.raildraw_loop_after
    arrow_width, arrow_height = options.raildraw_size_of_arrow(options)
    width = radius * 2 + arrow_width + before + max(c_width, d_width) + after + arrow_width + radius * 2
    height = c_height + options.raildraw_loop_spacing + d_height
    line_pos = c_line_pos
    return width, height, line_pos


@f(draw_functions, rr.Loop)
def draw_Loop(context, x, y, construct, options, forward):
    component = construct.component
    delimiter = construct.delimiter
    c_width, c_height, c_line_pos = size_of(context, component, options)
    d_width, d_height, d_line_pos = size_of(context, delimiter, options)
    c_arrow = not isinstance(component, rr.Nothing)
    d_arrow = not isinstance(delimiter, rr.Nothing)
    # For now, if the delimiter is Nothing, don't draw the component's arrows
    if not d_arrow:
        c_arrow = False
    spacing = options.raildraw_loop_spacing
    radius = options.raildraw_loop_radius
    before = options.raildraw_loop_before
    after = options.raildraw_loop_after
    arrow_width, arrow_height = options.raildraw_size_of_arrow(options)
    d_y = y + c_height + spacing
    width, height, line_pos = size_of_Loop(context, construct, options)
    max_width = max(c_width, d_width)
    center_x = x + radius * 2 + arrow_width + before + (max_width / 2)
    draw_line(context, x, y + line_pos, x + radius * 2, y + line_pos)
    draw_arrow_or_line(context, x + radius * 2, y + line_pos - arrow_height / 2, arrow_width, arrow_height, options, forward, c_arrow)
    draw_line(context, x + radius * 2 + arrow_width, y + line_pos, center_x - c_width / 2, y + line_pos)
    draw(context, center_x - c_width / 2, y, component, options, forward)
    draw_line(context, center_x + c_width / 2, y + line_pos, x + width - radius * 2 - arrow_width, y + line_pos)
    draw_arrow_or_line(context, x + width - radius * 2 - arrow_width, y + line_pos - arrow_height / 2, arrow_width, arrow_height, options, forward, c_arrow)
    draw_line(context, x + width - radius * 2, y + line_pos, x + width, y + line_pos)
    # Component and its two arrows and line drawn. Now draw the curve down and
    # the delimiter, and its arrows and lines.
    context.move_to(x + radius * 2, y + line_pos)
    context.arc_negative(x + radius * 2, y + line_pos + radius, radius, radians(270), radians(180))
    context.line_to(x + radius, d_y + d_line_pos - radius)
    context.arc_negative(x + radius * 2, d_y + d_line_pos - radius, radius, radians(180), radians(90))
    context.stroke()
    draw_arrow_or_line(context, x + radius * 2, d_y + d_line_pos - arrow_height / 2, arrow_width, arrow_height, options, not forward, d_arrow)
    draw_line(context, x + radius * 2 + arrow_width, d_y + d_line_pos, center_x - d_width / 2, d_y + d_line_pos)
    draw(context, center_x - d_width / 2, d_y, delimiter, options, not forward)
    draw_line(context, center_x + d_width / 2, d_y + d_line_pos, x + width - radius * 2 - arrow_width, d_y + d_line_pos)
    draw_arrow_or_line(context, x + width - radius * 2 - arrow_width, d_y + d_line_pos - arrow_height / 2, arrow_width, arrow_height, options, not forward, d_arrow)
    context.move_to(x + width - radius * 2, d_y + d_line_pos)
    context.arc_negative(x + width - radius * 2, d_y + d_line_pos - radius, radius, radians(90), radians(0))
    context.line_to(x + width - radius, y + line_pos + radius)
    context.arc_negative(x + width - radius * 2, y + line_pos + radius, radius, radians(0), radians(270))
    context.stroke()


# FIXME: Test loops with components and delimiters that have different heights
# and different line positions


def draw_arrow_or_line(context, x, y, arrow_width, arrow_height, options, forward, arrow):
    if arrow:
        options.raildraw_draw_arrow(context, x, y, options, forward)
    else:
        draw_line(context, x, y + arrow_height / 2, x + arrow_width, y + arrow_height / 2)


@f(size_functions, rr.Bullet)
def size_of_Bullet(context, construct, options):
    diameter = options.raildraw_bullet_radius * 2
    return diameter, diameter, diameter / 2


@f(draw_functions, rr.Bullet)
def draw_Bullet(context, x, y, construct, options, forward):
    radius = options.raildraw_bullet_radius
    context.move_to(x + radius * 2, y + radius)
    context.arc(x + radius, y + radius, radius, radians(0), radians(360))
    context.stroke()


del f


def draw_text(context, x, y, font, text):
    layout = PangoCairo.create_layout(context)
    layout.set_text(text, -1)
    layout.set_font_description(font)
    context.move_to(x, y)
    PangoCairo.show_layout(context, layout)
    return layout.get_pixel_size()


def draw_to_surface(surface_cb, diagram, options, filename, forward=True):
    """
    Draws the specified railroad diagram, which should be an instance of
    parcon.railroad.Component or one of its subclasses, or a dictionary, into
    the PNG file at the specified file name.
    
    If the specified diagram is a dict, each of the diagrams contained as its
    values will be drawn into the file, top to bottom, with the corresponding
    keys (which should be strings) used as titles before each diagram.
    
    You can either manually create instances of any of
    parcon.railroad.Component's subclasses to pass to this method, or you can
    convert a Parcon parser to a Component by calling its create_railroad
    method.
    
    options is a dictionary of options to use. For now, just use the empty
    dict; I'll get around to documenting the options that you can use here at
    some point.
    """
    if not isinstance(diagram, dict):
        diagram = {"": diagram}
    options = create_options(options)
    before_title = options.raildraw_title_before
    after_title = options.raildraw_title_after
    # Create an empty image to give size_of something to reference
    empty_image = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1, 1)
    empty_context = cairo.Context(empty_image)
    width, height = 0, 0
    for name, d in diagram.items():
        w, h, l = size_of(empty_context, d, options)
        width, height = max(width, w), h + height
    height += len(diagram) * (before_title + after_title)
    image = surface_cb(int((width + 16) * options.raildraw_scale),
                       int((height + 16) * options.raildraw_scale))
    context = cairo.Context(image)
    if options.raildraw_scale != 1:
        context.scale(options.raildraw_scale, options.raildraw_scale)
    x = 8
    y = 8
    for name, d in diagram.items():
        if not options.raildraw_title_hide:
            draw_text(context, x, y, options.raildraw_title_font, name + ":")
        y += after_title
        draw_to_context(context, d, options, filename, forward, x, y)
        # FIXME: store the size as computed 10 or 20 lines above to avoid
        # having to compute it twice
        y += size_of(context, d, options)[1]
        y += before_title

def draw_to_png(diagram, options, filename, forward):
    image_ref = [0]
    def get_surface_cb(image_ref):
        def get_surface(width,height):
            image_ref[0] = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
            return image_ref[0]
        return get_surface
    draw_to_surface(get_surface_cb(image_ref), diagram, options, filename, forward)
    image_ref[0].write_to_png(filename)

def draw_to_svg(diagram, options, filename, forward):
    def get_surface(width, height):
        return cairo.SVGSurface(filename, width, height)
    draw_to_surface(get_surface, diagram, options, filename, forward)

def draw_to_image(img_type, diagram, options, filename, forward=True):
    if img_type == 'png':
        draw_to_png(diagram, options, filename, forward)
    elif img_type == 'svg':
        draw_to_svg(diagram, options, filename, forward)
    else:
        raise Exception("No such image type")

def draw_to_context(context, diagram, options, filename, forward=True, x=8, y=8):
    """
    Same as draw_to_png, but draws the specified railroad diagram to a context,
    which should be an instance of cairo.Context, instead of to a PNG file.
    draw_to_png actually delegates to this function to do the actual drawing.
    
    x and y are the position at which to draw the specified diagram.
    """
    diagram = diagram.copy()
    diagram.optimize()
    context.set_line_width(options.raildraw_line_size)
    draw(context, x, y, diagram, options, forward)
    






































