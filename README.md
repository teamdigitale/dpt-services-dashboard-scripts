# Dashboards data ingestion scripts for Digital Transformation Department

The scripts in this repository are used to collect data from different, external sources and store them in a MongoDB database.

## The Italian Department of Digital Transformation

More informations about the Italian Department of Innovation can be found on the Department [website](https://innovazione.gov.it/)

## What the dashboard data ingestion scripts do?

The scripts in this repository are used to collect data from different external sources and store them in a MongoDB database.

## How to build and test the scripts

The dashboard scripts container and the related visualization tools are distributed as a set of Docker containers interacting with one each other.

The `Dockerfile` and the `docker-compose.yaml` files are in the root of this repository.

To build the local test environment run:

```shell
docker-compose up -d
```

>NOTE: the `docker-compose.yaml` file sets different environment variables that could be used to adapt and customized many platform functionalities.

While the ingestion scripts are called on a regular basis in production, in this test environment they need to be called manually, so that some test data can be manually sourced and injected into MongoDB (see how in the paragraphs below).

Also, once the build process is complete, the Metabase dashboard can be accessed at `http://localhost:3000`.

> NOTE: Credentials should be changed after the first login.

>NOTE: the `/data` folder contains dummy data, useful to be able to carry out tests.

To bring down the test environment and remove the containers use

```shell
docker-compose down
```

## How to contribute

Contributions are welcome. Feel free to [open issues](./issues) and submit a [pull request](./pulls) at any time.

## License

Copyright (c) 2020 Presidenza del Consiglio dei Ministri

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program.  If not, see <https://www.gnu.org/licenses/>.
