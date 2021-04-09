# Dashboards data ingestion scripts for Digital Transformation Department

Scripts to collect data from different, external sources and store them in a
MongoDB database.

Also contains `italian_regions.geojson`, used as a custom region map in our
production instance of Metabase.

## How to build and test the scripts

To build the local test environment run:

```shell
docker-compose up -d
```

> NOTE: you can set environment variables in the `.env` file. See `.env.example`.

While the ingestion scripts are called on a regular basis in production, in this
test environment they need to be called manually, so that some test data can be
manually sourced and injected into MongoDB (see how in the paragraphs below).

Once the build process is complete, the Metabase dashboard can be accessed at `http://localhost:3000`.

>NOTE: the `/data` folder contains dummy data, useful to be able to carry out tests.

To bring down the test environment and remove the containers use

```shell
docker-compose down
```

## How to contribute

Contributions are welcome. Feel free to [open issues](./issues) or submit a
[pull request](./pulls) at any time.

## License

Copyright ⓒ 2020 Presidenza del Consiglio dei Ministri

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU Affero General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option)
any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for
more details.

You should have received a copy of the GNU Affero General Public License along
with this program.  If not, see <https://www.gnu.org/licenses/>.
