pipeline {
    agent {
        kubernetes {
            // Описываем под прямо в коде — это гарантирует, что пайплайн запустится везде одинаково
            yaml """
apiVersion: v1
kind: Pod
metadata:
  labels:
    component: jenkins-agent
spec:
  # Наш настроенный контекст безопасности для доступа к сокету
  securityContext:
    runAsUser: 1000
    runAsGroup: 1000
    supplementalGroups: [984]
  containers:
  # Основной контейнер со встроенной утилитой docker
  - name: docker-cli
    image: docker:24.0.7-cli
    command: ['cat']
    tty: true
    volumeMounts:
    - mountPath: /var/run/docker.sock
      name: docker-sock
  volumes:
  - name: docker-sock
    hostPath:
      path: /var/run/docker.sock
"""
        }
    }

    environment {
        NEXUS_URL = 'host.k3d.internal:5000'
        IMAGE_NAME = 'myapp-flask'
    }

    stages {
        stage('Checkout') {
            steps {
                script { 
                    checkout scm
                    env.COMMIT = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                // Говорим Дженкинсу выполнять сборку внутри контейнера docker-cli
                container('docker-cli') {
                    script {
                        sh "docker build -t ${IMAGE_NAME}:${COMMIT} ."
                    }
                }
            }
        }

        stage('Push to Nexus') {
            steps {
                container('docker-cli') {
                    script {
                        sh "docker tag ${IMAGE_NAME}:${COMMIT} ${NEXUS_URL}/${IMAGE_NAME}:${COMMIT}"
                        withCredentials([usernamePassword(
                            credentialsId: 'nexus-creds',
                            usernameVariable: 'NEXUS_USER',
                            passwordVariable: 'NEXUS_PASS'
                        )]) {
                            sh "docker login -u ${NEXUS_USER} -p ${NEXUS_PASS} ${NEXUS_URL}"
                            sh "docker push ${NEXUS_URL}/${IMAGE_NAME}:${COMMIT}"
                        }
                    }
                }
            }
        }

        stage('Update GitOps') {
            steps {   
                script {
                    sshagent(['git-key']) {
                        sh """
                            rm -rf gitops-tmp
                            git -c core.sshCommand="ssh -o StrictHostKeyChecking=no" clone git@github.com:endlessfire1/gitops.git gitops-tmp
                            cd gitops-tmp
                            sed -i "s|image: .*|image: ${NEXUS_URL}/${IMAGE_NAME}:${COMMIT}|g" apps/myapp/deployment.yaml
                            git config user.name "Jenkins CI"
                            git config user.email "jenkins@local"
                            git add .
                            git commit -m "Update image to ${COMMIT} [skip ci]"
                            git push origin main
                        """
                    }
                }
            }
        }
    }

    post {
        always {
            sh "rm -rf gitops-tmp"
        }
    }
}
