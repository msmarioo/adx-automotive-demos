// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
require('dotenv').config();
var express = require('express');
var router = express.Router();
const kusto = require('../kusto.js');
const mapKey = process.env.AZURE_MAPS_KEY;

/* GET home page. */
router.get('/', function(req, res, next) {
  res.render('index', { title: 'Fleet Analytics' });   
});

router.get('/heatmap', function(req, res, next) {
  res.render('heatmap', { title: 'Heatmap', key: mapKey });   
});

router.get('/fares', function(req, res, next) {
  res.render('fares', { title: 'Fares', key: mapKey  });   
});

router.get('/geospatial/fares', function(req, res, next) {
  kusto.queryFares().then(result => {     
    var geoJSON = result.primaryResults[0][0].raw[0];
    res.json(geoJSON);    
  });
});

router.get('/geospatial/location_heatmap', function(req, res, next) {
  kusto.queryLocationHeatmap().then(result => {   
    var geoJSON = result.primaryResults[0][0].raw[0];
    res.json(geoJSON);
  });
});

module.exports = router;
