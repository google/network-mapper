# Tests for the Graph visualizer
# Should be run with:
#   casperjs test ${file}

# requirejs = require('./requiresjs')

require '../conf/test'

# require = patchRequire(global.require)
# casper = require('casper').create()
# console.log global.require
# console.log casper.options.clientScripts

# casper.options.clientScripts = [
# '../graph.coffee'
# ]

suite = (test) ->
  test.assert 1 is 1
  test.done()

require 'mocha'
require 'should'
g = require '../graph.coffee'

console.log g

describe 'Helper Functions', ->
  it 'should return the query string', ->
    [1, 2].length.should.equal 2
# casper.test.begin 'Testing graph.coffee...', 1, suite
# casper.test.done()
