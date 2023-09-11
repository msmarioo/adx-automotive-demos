// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.
require('dotenv').config();
const KustoClient = require("azure-kusto-data").Client;
const KustoConnectionStringBuilder = require("azure-kusto-data").KustoConnectionStringBuilder;
const ClientRequestProperties = require("azure-kusto-data").ClientRequestProperties;
const { v4: uuidv4 } = require('uuid');


const clusterConnectionString = process.env.CLUSTER_CONNECTION_STRING;
const database = process.env.DATABASE_NAME;


// -- Use Application authentication for non-demo purposes --
// -- the appid parameter is the Application (client) ID guid from the overview page of the app registration
// -- the tenantID parameter is the Directory (tenant) ID guid from the overview page of the app registration
// const aadAppId = process.env.AAD_APP_ID; 
// const appKey = process.env.AAD_APP_KEY;
// const tenantID = process.env.AAD_TENANT_ID; 
// const kcs = KustoConnectionStringBuilder.withAadApplicationKeyAuthentication(clusterConnectionString, aadAppId, appKey, tenantID);

// -- For dev purposes you can use AZ Device Authentication  --
const kcs = KustoConnectionStringBuilder.withAadDeviceAuthentication(clusterConnectionString)

const kustoClient = new KustoClient(kcs);

// The following queries assume the use of the NYC open taxy data set.

/**
 * Returns fare statistics per cell.
 * This query will show statistics (avg, min, max) for the fare amount + tip grouped by geocell.
 * All locations with less than 10 events are filtered out from the query. 
 * 
 * @returns A KustoResultDataSet containing the query results
 */
module.exports.queryFares = async function queryFares() {
    const kqlQuery = `
    let now = now();
    let dayokweektoday = dayofweek(now);
    let hourofdaytoday = hourofday(now);
    Trips
    | where dayofweek(pickup_datetime) == dayokweektoday
    | where hourofday(pickup_datetime) == hourofdaytoday 
    | where isnotempty(pickup_longitude)
    | where isnotempty(pickup_latitude)
    | extend h3cell = geo_point_to_h3cell(pickup_longitude, pickup_latitude, 10)
    | summarize eventCount=count(), average=avg(fare_amount + tip_amount), max=max(fare_amount + tip_amount), min=min(fare_amount + tip_amount) by h3cell
    | where eventCount > 10
    | project h3_hash_polygon = geo_h3cell_to_polygon(h3cell), telemetry = pack_all(), h3cell
    | project feature=bag_pack(
            "type", "Feature",
            "geometry", h3_hash_polygon,
            "properties", telemetry)
    | summarize features = make_list(feature)
    | project bag_pack(
            "type", "FeatureCollection",
            "features", features) 
    `;
    return query(kqlQuery);
}

/**
 * Count of pick-up events per cell.
 * This query will show the number of taxi pickups for the current day of the week and hour of the day.
 * @returns A KustoResultDataSet containing the query results 
 */
module.exports.queryLocationHeatmap = async function queryLocationHeatmap() {
    const kqlQuery = `
    let now = now();
    let dayokweektoday = dayofweek(now);
    let hourofdaytoday = hourofday(now);
    Trips
    | where dayofweek(pickup_datetime) == dayokweektoday
    | where hourofday(pickup_datetime) == hourofdaytoday 
    | extend h3cell = geo_point_to_h3cell(pickup_longitude, pickup_latitude, 12)
    | summarize eventCount=count() by h3cell
    | where eventCount > 10
        | project h3_hash_polygon = geo_h3cell_to_polygon(h3cell), telemetry = pack_all(), h3cell
        | project feature=bag_pack(
                "type", "Feature",
                "geometry", h3_hash_polygon,
                "properties", telemetry)
        | summarize features = make_list(feature)
        | project bag_pack(
                "type", "FeatureCollection",
                "features", features) 
    `;
    return query(kqlQuery);
}

/**
 * The query function will execute a query against the Azure Data Explorer Database.
 * This method is only used internally, as the queries are predefined.
 * 
 * @param {*} query the KUSTO Query
 * @returns A KustoResultDataSet containing the query results
 */
async function query(query) {
    try {

        // providing ClientRequestProperties
        // for a complete list of ClientRequestProperties
        // go to https://docs.microsoft.com/en-us/azure/kusto/api/netfx/request-properties#list-of-clientrequestproperties
        let clientRequestProps = new ClientRequestProperties();
        const oneMinute = 1000 * 60;
        clientRequestProps.setTimeout(oneMinute);

        // having client code provide its own clientRequestId is
        // highly recommended. It not only allows the caller to
        // cancel the query, but also makes it possible for the Kusto
        // team to investigate query failures end-to-end:
        clientRequestProps.clientRequestId = `FleetVisualization.Query;${uuidv4()}`;

        const results = await kustoClient.execute(database, query, clientRequestProps);

        return results;

    }
    catch (error) {
        console.log(error);
    }

}