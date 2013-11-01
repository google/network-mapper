/** Local test-rig configuration file. */
var requirejs = require('requirejs');

requirejs.config({
  baseUrl: '../',
  paths: {
    jquery: 'vendor/jquery',
    cs: 'vendor/cs',
    'coffee-script': 'vendor/coffee',
    bootstrap: 'vendor/bootstrap',
    domReady: 'vendor/domReady',
    d3: 'vendor/d3',
    modernizr: 'vendor/modernizr',
    backbone: 'vendor/backbone',
    underscore: 'vendor/underscore',
    // mocha: 'vendor/mocha'
    amdefine: 'vendor/amdefine',
  },
  shim: {
    jquery: {
      exports: 'jQuery'
    },
    bootstrap: {
      deps: ['jquery']
    },
    d3: {
      exports: 'd3'
    },
    modernizr: {
      exports: 'Modernizr'
    }
  }
});

global.define = require('requirejs');

exports.require = requirejs;
