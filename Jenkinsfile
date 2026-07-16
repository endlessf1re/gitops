pipeline {
    agent {
        kubernetes {
            yaml """
apiVersion: v1
kind: Pod
metadata:
  labels:
    component: jenkins-agent
spec:
  containers:
  - name: docker-cli
    image: docker:24.0.7-cli
    imagePullPolicy: IfNotPresent
    command: ['cat']
    tty: true
    env:
    - name: DOCKER_HOST
      value: tcp://localhost:2375
  - name: dind
    image: docker:24.0.7-dind
    securityContext:
      privileged: true
    env:
    - name: DOCKER_TLS_CERTDIR
      value: ""
    volumeMounts:
    - name: docker-storage
      mountPath: /var/lib/docker
  volumes:
  - name: docker-storage
    emptyDir: {}
"""
        }
    }
    environment {
        NEXUS_URL = 'host.k3d.internal:8083'
        IMAGE_NAME = 'myapp-flask'
        DOCKER_CONFIG = '/tmp/docker-config'   // доступно для записи
        DOCKER_BUILDKIT = '0'
    }
    stages {
        stage('Checkout') {
            steps {
                script {
                    checkout scm
                    env.COMMIT = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    echo "COMMIT = ${env.COMMIT}"
                    echo "IMAGE_NAME = ${env.IMAGE_NAME}"
                }
            }
        }
        stage('Prepare Docker Config') {
            steps {
                container('docker-cli') {
                    script {
                        sh """
                            mkdir -p ${DOCKER_CONFIG}
                            chmod 700 ${DOCKER_CONFIG}
                        """
                    }
                }
            }
        }
        stage('Wait for Docker daemon') {
            steps {
                container('docker-cli') {
                    sh '''
                        echo "Waiting for docker daemon..."
                        for i in $(seq 1 30); do
                            if docker info >/dev/null 2>&1; then
                                echo "Docker daemon is ready"
                                exit 0
                            fi
                            echo "Attempt $i/30: daemon not ready yet, sleeping 2s..."
                            sleep 2
                        done
                        echo "Docker daemon did not become ready in time"
                        exit 1
                    '''
                }
            }
        }
