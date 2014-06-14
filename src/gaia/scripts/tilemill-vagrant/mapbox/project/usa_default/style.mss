@land: #faefe7;
@water: #88cfda;
@waterline: #757573;

Map {
  background-color: @water;
}

#countries {
  ::outline {
    line-color: #85c5d3;
    line-width: 2;
    line-join: round;
  }
  ::fill {
  	polygon-fill:@land;
  	polygon-gamma:0.75;
  	[ADM0_A3='USA'] { polygon-fill:lighten(@land, 5); }
  }
}

#countries::outline {
  line-color:@waterline;
  line-width:1.6;
}
#countries::fill {
  polygon-fill:@land;
  polygon-gamma:0.75;
  [ADM0_A3='USA'] { polygon-fill:lighten(@land, 7); }
}

#state_line {
  line-width:1;
  line-opacity:0.2;
  line-color:#7d8385;
}

#country_border {
  line-color:#9c8928;
}

#country_border[zoom<3] { line-width:0.4; }
#country_border[zoom=3] { line-width:0.8; }
#country_border[zoom=4] { line-width:1.2; }
#country_border[zoom=5] { line-width:1.6; }

#country_border_marine {
  line-color:#A06;
  line-dasharray:8,2;
  line-opacity:0.2;
  line-width:0.8;
}

