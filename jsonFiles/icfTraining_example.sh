{
	"tag": "TAG",
	"glueCodeMode": 0,
	"solverCode": 0,
	"SchedulerInterface": 0,
	"ProvisioningInterface": 1,
	"ICFParameters":{
		"RelativeError": 0.0001
	},
	"SlurmScheduler":{
		"ThreadsPerMPIRankForSlurm": 1,
		"NodesPerSlurmJob": 1,
		"MaxSlurmJobs": 1,
		"SlurmPartition": "general"
	},
"SpackVariables":{
		"SpackRoot": "/opt/spack",
		"SpackCompilerAndMPI": "%gcc@7.3.0 ^openmpi@3.1.3%gcc@7.3.0",
		"SpackLAMMPS": "lammps+mpi~ffmpeg"
	},
	"SpackCompilerAndMPI": "%gcc@7.3.0 ^openmpi@3.1.3%gcc@7.3.0",
	"alBackend": 3,
	"ActiveLearningVariables":{
		"GNDthreshold": 20,
		"NumberOfRequestingActiveLearners": 1
	},
	"DatabaseSettings":{
		"CoarseGrainDB":{
			"DatabaseMode": 0,
			"DatabaseURL": "testDB.db"
		},
		"FineGrainDB":{
			"DatabaseMode": 0,
			"DatabaseURL": "otherTestDB.db"
		}
	},
	"ExpectedMPIRanks": 1,
	"GenerateTrainingData": true,
	"DatabaseSettings":{
		"CoarseGrainDB":{
			"DatabaseMode": 0,
			"DatabaseURL": "testDB.db"
		},
		"FineGrainDB":{
			"DatabaseMode": 0,
			"DatabaseURL": "otherTestDB.db"
		}
	}
}
