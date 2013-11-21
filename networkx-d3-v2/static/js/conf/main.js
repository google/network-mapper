require.config( {
  baseUrl: '/static/js',
  paths: {
    domReady: 'vendor/domReady',
    jquery: 'vendor/jquery',
    underscore: 'vendor/underscore',
    d3: 'vendor/d3',
    modernizr: 'vendor/modernizr',
    backbone: 'vendor/backbone',
    canvg: 'vendor/canvg',
    cs: 'vendor/cs',
    'coffee-script': 'vendor/coffee'
  },
  shim: {
    jquery: {
      exports: 'jquery'
    },
    d3: {
      exports: 'd3'
    },
    modernizr: {
      exports: 'Modernizr'
    }
  }
});
