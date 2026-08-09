%!PS-Adobe-3.0
%%Creator: (ImageMagick)
%%Title: (re)
%%CreationDate: (2026-08-09T00:36:41-03:00)
%%BoundingBox: 476 85 486 110
%%HiResBoundingBox: 476 85 486 110
%%DocumentData: Clean7Bit
%%LanguageLevel: 1
%%Orientation: Portrait
%%PageOrder: Ascend
%%Pages: 1
%%EndComments

%%BeginDefaults
%%EndDefaults

%%BeginProlog
%
% Display a color image.  The image is displayed in color on
% Postscript viewers or printers that support color, otherwise
% it is displayed as grayscale.
%
/DirectClassPacket
{
  %
  % Get a DirectClass packet.
  %
  % Parameters:
  %   red.
  %   green.
  %   blue.
  %   length: number of pixels minus one of this color (optional).
  %
  currentfile color_packet readhexstring pop pop
  compression 0 eq
  {
    /number_pixels 3 def
  }
  {
    currentfile byte readhexstring pop 0 get
    /number_pixels exch 1 add 3 mul def
  } ifelse
  0 3 number_pixels 1 sub
  {
    pixels exch color_packet putinterval
  } for
  pixels 0 number_pixels getinterval
} bind def

/DirectClassImage
{
  %
  % Display a DirectClass image.
  %
  systemdict /colorimage known
  {
    columns rows 8
    [
      columns 0 0
      rows neg 0 rows
    ]
    { DirectClassPacket } false 3 colorimage
  }
  {
    %
    % No colorimage operator;  convert to grayscale.
    %
    columns rows 8
    [
      columns 0 0
      rows neg 0 rows
    ]
    { GrayDirectClassPacket } image
  } ifelse
} bind def

/GrayDirectClassPacket
{
  %
  % Get a DirectClass packet;  convert to grayscale.
  %
  % Parameters:
  %   red
  %   green
  %   blue
  %   length: number of pixels minus one of this color (optional).
  %
  currentfile color_packet readhexstring pop pop
  color_packet 0 get 0.299 mul
  color_packet 1 get 0.587 mul add
  color_packet 2 get 0.114 mul add
  cvi
  /gray_packet exch def
  compression 0 eq
  {
    /number_pixels 1 def
  }
  {
    currentfile byte readhexstring pop 0 get
    /number_pixels exch 1 add def
  } ifelse
  0 1 number_pixels 1 sub
  {
    pixels exch gray_packet put
  } for
  pixels 0 number_pixels getinterval
} bind def

/GrayPseudoClassPacket
{
  %
  % Get a PseudoClass packet;  convert to grayscale.
  %
  % Parameters:
  %   index: index into the colormap.
  %   length: number of pixels minus one of this color (optional).
  %
  currentfile byte readhexstring pop 0 get
  /offset exch 3 mul def
  /color_packet colormap offset 3 getinterval def
  color_packet 0 get 0.299 mul
  color_packet 1 get 0.587 mul add
  color_packet 2 get 0.114 mul add
  cvi
  /gray_packet exch def
  compression 0 eq
  {
    /number_pixels 1 def
  }
  {
    currentfile byte readhexstring pop 0 get
    /number_pixels exch 1 add def
  } ifelse
  0 1 number_pixels 1 sub
  {
    pixels exch gray_packet put
  } for
  pixels 0 number_pixels getinterval
} bind def

/PseudoClassPacket
{
  %
  % Get a PseudoClass packet.
  %
  % Parameters:
  %   index: index into the colormap.
  %   length: number of pixels minus one of this color (optional).
  %
  currentfile byte readhexstring pop 0 get
  /offset exch 3 mul def
  /color_packet colormap offset 3 getinterval def
  compression 0 eq
  {
    /number_pixels 3 def
  }
  {
    currentfile byte readhexstring pop 0 get
    /number_pixels exch 1 add 3 mul def
  } ifelse
  0 3 number_pixels 1 sub
  {
    pixels exch color_packet putinterval
  } for
  pixels 0 number_pixels getinterval
} bind def

/PseudoClassImage
{
  %
  % Display a PseudoClass image.
  %
  % Parameters:
  %   class: 0-PseudoClass or 1-Grayscale.
  %
  currentfile buffer readline pop
  token pop /class exch def pop
  class 0 gt
  {
    currentfile buffer readline pop
    token pop /depth exch def pop
    /grays columns 8 add depth sub depth mul 8 idiv string def
    columns rows depth
    [
      columns 0 0
      rows neg 0 rows
    ]
    { currentfile grays readhexstring pop } image
  }
  {
    %
    % Parameters:
    %   colors: number of colors in the colormap.
    %   colormap: red, green, blue color packets.
    %
    currentfile buffer readline pop
    token pop /colors exch def pop
    /colors colors 3 mul def
    /colormap colors string def
    currentfile colormap readhexstring pop pop
    systemdict /colorimage known
    {
      columns rows 8
      [
        columns 0 0
        rows neg 0 rows
      ]
      { PseudoClassPacket } false 3 colorimage
    }
    {
      %
      % No colorimage operator;  convert to grayscale.
      %
      columns rows 8
      [
        columns 0 0
        rows neg 0 rows
      ]
      { GrayPseudoClassPacket } image
    } ifelse
  } ifelse
} bind def

/DisplayImage
{
  %
  % Display a DirectClass or PseudoClass image.
  %
  % Parameters:
  %   x & y translation.
  %   x & y scale.
  %   label pointsize.
  %   image label.
  %   image columns & rows.
  %   class: 0-DirectClass or 1-PseudoClass.
  %   compression: 0-none or 1-RunlengthEncoded.
  %   hex color packets.
  %
  gsave
  /buffer 512 string def
  /byte 1 string def
  /color_packet 3 string def
  /pixels 768 string def

  currentfile buffer readline pop
  token pop /x exch def
  token pop /y exch def pop
  x y translate
  currentfile buffer readline pop
  token pop /x exch def
  token pop /y exch def pop
  currentfile buffer readline pop
  token pop /pointsize exch def pop
  x y scale
  currentfile buffer readline pop
  token pop /columns exch def
  token pop /rows exch def pop
  currentfile buffer readline pop
  token pop /class exch def pop
  currentfile buffer readline pop
  token pop /compression exch def pop
  class 0 gt { PseudoClassImage } { DirectClassImage } ifelse
  grestore
  showpage
} bind def
%%EndProlog
%%Page:  1 1
%%PageBoundingBox: 476 85 486 110
DisplayImage
476 85
10 25
12
10 25
0
0
D8D2D8272D27272D27272D27272D27272D27272D27272D27272D27D8D2D8D8D0D8272F27272F27
272F27272F27272F27272F27272F27272F27D8D0D8DAD0DA252F25252F25252F25252F25252F25
252F25252F25252F25DAD0DADACCDA253325253325253325253325253325253325253325253325
DACCDADBCADB243524243524243524243524243524243524243524243524DBCADBCEBACE314531
314531314531314531314531314531314531314531CEBACED0B8D02F472F2F472F2F472F2F472F
2F472F2F472F2F472F2F472FD0B8D0D1B6D12E492E2E492E2E492E2E492E2E492E2E492E2E492E
2E492ED1B6D1D3B2D32C4D2C2C4D2C2C4D2C2C4D2C2C4D2C2C4D2C2C4D2C2C4D2CD3B2D3D5B1D5
2A4E2A2A4E2A2A4E2A2A4E2A2A4E2A2A4E2A2A4E2A2A4E2AD5B1D5E5DADE1A25211A25211A2521
1A25211A25211A25211A25211A2521E5DADE544739ABB8C6ABB8C6ABB8C6ABB8C6ABB8C6ABB8C6
ABB8C6ABB8C6544739AFA69B505964505964505964505964505964505964505964505964AFA69B
AFA69B505964505964505964505964505964505964505964505964AFA69BAFA69B505964505964
505964505964505964505964505964505964AFA69BAFA69B505964505964505964505964505964
505964505964505964AFA69BAFA69B505964505964505964505964505964505964505964505964
AFA69BAFA69B505964505964505964505964505964505964505964505964AFA69BAFA69B505964
505964505964505964505964505964505964505964AFA69BAFA69B505964505964505964505964
505964505964505964505964AFA69BC1B8AD3E47523E47523E47523E47523E47523E47523E4752
3E4752C1B8ADAFA69B505964505964505964505964505964505964505964505964AFA69BAFA69B
505964505964505964505964505964505964505964505964AFA69BAFA69B505964505964505964
505964505964505964505964505964AFA69BAFA69BAFA69BAFA69BAFA69BAFA69BAFA69BAFA69B
AFA69BAFA69B505964

%%PageTrailer
%%Trailer
%%EOF
