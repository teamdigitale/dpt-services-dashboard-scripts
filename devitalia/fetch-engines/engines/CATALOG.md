# Catalog

This section contains all the scripts to export statistics for the 
open source software catalog

## Export statistics

You can run this script to export statistics in a csv file (`catalog.csv`)

```bash
python3 main.py  -t catalogo --data_dir . --num_threads "1"
```

or use `devitalia/process.sh` script to import data inside MongoDB.

## 

Exported data are grouped by crawling date and contain

- The total number of PAs.
- The total number of softwares.
- The total number of softwares released for reuse.

Note that this data should be represented as a percentage, to achieve this inside Metabase you should use the following custom query.

```bash
[
    { $match: {} },
    { $group: { _id : null, software_total : { $sum: "$num_softwares" }, num_reuse : { $sum: "$num_softwares_reuse" } }},
    { $project: { 
        _id : 0, num_reuse_percent : { 
            $divide: [ "$num_reuse", "$software_total"]
        }
      }
    },
]
```

- The total number of softwares reused at least once.

Note that this data should be represented as a percentage, to achieve this inside Metabase you should use the following custom query.

```bash
[
    { $match: {} },
    { $group: { _id : null, software_total : { $sum: "$num_softwares" }, num_reusing : { $sum: "$num_softwares_reusing" } }},
    { $project: { 
        _id : 0, num_reusing_percent : { 
            $divide: [ "$num_reusing", "$software_total"]
        }
      }
    },
]
```

- The total software vitality.
- The total number of PAs reusing software.