pipeline {
    agent any

    environment{
        BUILD_TAG = "${env.BUILD_NUMBER}"
        PROJECT_NAME = "corso-devops"
        PATH= "${JENKINS_HOME}/bin:${env.PATH}"
        AWS_REGION    = 'eu-central-1'
    }

    options {
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '10'))

        timestamps()
    }

    parameters{
        booleanParam(name: 'SKIP_TESTS', defaultValue: false, description: 'Esegui i test dopo la build?')
        choice(name: 'Environment', choices: ['dev', 'staging', 'prod'], description: 'Seleziona l\'ambiente di deploy')
    
    }

    stages{
        stage('Checkout') {
            steps {
                checkout scm
 
                script {
                    env.GIT_SHORT_SHA = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
                    env.IMAGE_TAG     = "${BUILD_NUMBER}-${GIT_SHORT_SHA}"
                }
                        sh '''

                    echo "=========================================="
                    echo "  OrderFlow CI Pipeline"
                    echo "=========================================="
                    echo "Build:       #${BUILD_NUMBER}"
                    echo "Branch:      ${GIT_BRANCH}"
                    echo "Commit:      $(git log --oneline -1)"
                    echo "Environment: ${ENVIRONMENT}"
                    echo "=========================================="

                '''
 
            echo "Checkout completato"
            }
        }

        stage('Setup Tools') {
            steps {
                sh '''
                    echo "=== Installing required tools ==="
                    TOOLS_DIR="${JENKINS_HOME}/bin"
                    mkdir -p "${TOOLS_DIR}"
 
                    # AWS CLI v2
                    if [ -x "${TOOLS_DIR}/aws" ]; then
                        echo "PASS: AWS CLI already installed ($(${TOOLS_DIR}/aws --version))"
                    else
                        echo "Installing AWS CLI v2..."
                        curl -sL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "/tmp/awscliv2.zip"
                        unzip -qo /tmp/awscliv2.zip -d /tmp
                        /tmp/aws/install --install-dir "${TOOLS_DIR}/aws-cli" --bin-dir "${TOOLS_DIR}" --update
                        rm -rf /tmp/awscliv2.zip /tmp/aws
                        echo "Installed: $(aws --version)"
                    fi

                    if ! command -v docker-compose >/dev/null 2>&1; then
                        echo "Installazione docker-compose..."
                        curl -L "https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-$(uname -s)-$(uname -m)" -o "${TOOLS_DIR}/docker-compose"
                        chmod +x "${TOOLS_DIR}/docker-compose"
                        export PATH="${TOOLS_DIR}:$PATH"
                        echo "docker-compose installato: $(docker-compose --version)"
                    fi
                    echo "=== Tools ready ==="
                '''
            }
        }

        stage('Validation'){
            steps{
                sh '''
                    echo "=== Validating project structure ==="
                    ERRORS=0
                    for svc in order-service inventory-service notification-service; do
                        echo "--- Checking ${svc} ---"
                        if [ ! -d "${svc}" ]; then
                            echo "  FAIL: directory not found"
                            ERRORS=$((ERRORS + 1))
                            continue
                        fi
                        for f in Dockerfile requirements.txt main.py; do
                            if [ -f "${svc}/${f}" ]; then
                                echo "  ${f}: OK"
                            else
                                echo "  ${f}: MISSING"
                                ERRORS=$((ERRORS + 1))
                            fi
                        done
                    done
                    if [ ${ERRORS} -gt 0 ]; then
                        echo "Validation FAILED with ${ERRORS} errors"
                        exit 1
                    fi
                    echo "Validation PASSED"
                '''
            }
        }

        stage('Build Images') {
            parallel {
                stage('Build order-service') {
                    steps {
                        dir('order-service') {
                            sh 'docker build -t corso-devops/order-service:${IMAGE_TAG} -t corso-devops/order-service:latest .'
                        }
                    }
                }
                stage('Build inventory-service') {
                    steps {
                        dir('inventory-service') {
                            sh 'docker build -t corso-devops/inventory-service:${IMAGE_TAG} -t corso-devops/inventory-service:latest .'
                        }
                    }
                }
                stage('Build notification-service') {
                    steps {
                        dir('notification-service') {
                            sh 'docker build -t corso-devops/notification-service:${IMAGE_TAG} -t corso-devops/notification-service:latest .'
                        }
                    }
                }
            }
        }

        stage('Unit Tests') {
            parallel {
                stage('Test order-service') {
                    steps {
                        sh '''#!/bin/bash
                            set -eo pipefail
                            mkdir -p test-results
                            CONTAINER="test-order-${BUILD_NUMBER}"
                            docker rm -f "$CONTAINER" 2>/dev/null || true
                            docker create --name "$CONTAINER" --user root \
                                -e COVERAGE_FILE=/tmp/.coverage \
                                ${PROJECT_NAME}/order-service:latest \
                                sh -c "python -m pytest tests/ -v --tb=short \
                                    --junitxml=/tmp/order-results.xml \
                                    --cov=. --cov-report=term \
                                    --cov-fail-under=50"
                            docker start -a "$CONTAINER" 2>&1 | tee test-results/order-test.log
                            TEST_EXIT=${PIPESTATUS[0]}
                            docker cp "$CONTAINER":/tmp/order-results.xml test-results/ 2>/dev/null || true
                            docker rm "$CONTAINER" 2>/dev/null || true
                            exit $TEST_EXIT
                        '''
                    }
                }
                stage('Test inventory-service') {
                    steps {
                        sh '''#!/bin/bash
                            set -eo pipefail
                            mkdir -p test-results
                            CONTAINER="test-inventory-${BUILD_NUMBER}"
                            docker rm -f "$CONTAINER" 2>/dev/null || true
                            docker create --name "$CONTAINER" --user root \
                                -e COVERAGE_FILE=/tmp/.coverage \
                                ${PROJECT_NAME}/inventory-service:latest \
                                sh -c "python -m pytest tests/ -v --tb=short \
                                    --junitxml=/tmp/inventory-results.xml \
                                    --cov=. --cov-report=term \
                                    --cov-fail-under=50"
                            docker start -a "$CONTAINER" 2>&1 | tee test-results/inventory-test.log
                            TEST_EXIT=${PIPESTATUS[0]}
                            docker cp "$CONTAINER":/tmp/inventory-results.xml test-results/ 2>/dev/null || true
                            docker rm "$CONTAINER" 2>/dev/null || true
                            exit $TEST_EXIT
                        '''
                    }
                }
                stage('Test notification-service') {
                    steps {
                        sh '''#!/bin/bash
                            set -eo pipefail
                            mkdir -p test-results
                            CONTAINER="test-notification-${BUILD_NUMBER}"
                            docker rm -f "$CONTAINER" 2>/dev/null || true
                            docker create --name "$CONTAINER" --user root \
                                -e COVERAGE_FILE=/tmp/.coverage \
                                ${PROJECT_NAME}/notification-service:latest \
                                sh -c "python -m pytest tests/ -v --tb=short \
                                    --junitxml=/tmp/notification-results.xml \
                                    --cov=. --cov-report=term \
                                    --cov-fail-under=50"
                            docker start -a "$CONTAINER" 2>&1 | tee test-results/notification-test.log
                            TEST_EXIT=${PIPESTATUS[0]}
                            docker cp "$CONTAINER":/tmp/notification-results.xml test-results/ 2>/dev/null || true
                            docker rm "$CONTAINER" 2>/dev/null || true
                            exit $TEST_EXIT
                        '''
                    }
                }
            }
        }

        stage('Integration Test') {
            steps {
                sh '''
                    echo "=== Starting Integration Tests ==="

                    # 1. Start postgres first and wait for it to be healthy
                    docker-compose -f docker-compose.yml up -d postgres
                    echo "Waiting for postgres to be healthy..."
                    PGWAIT=0
                    while [ $PGWAIT -lt 60 ]; do
                        PG_STATUS=$(docker inspect --format='{{.State.Health.Status}}' orderflow-postgres 2>/dev/null || echo "missing")
                        echo "  [${PGWAIT}s] postgres: $PG_STATUS"
                        if [ "$PG_STATUS" = "healthy" ]; then
                            break
                        fi
                        sleep 3
                        PGWAIT=$((PGWAIT + 3))
                    done
                    if [ "$PG_STATUS" != "healthy" ]; then
                        echo "FAIL: postgres did not become healthy within 60s"
                        docker logs orderflow-postgres --tail 30 2>&1 || true
                        exit 1
                    fi

                    # 2. Start application services (postgres is already healthy)
                    docker-compose -f docker-compose.yml up -d order-service inventory-service notification-service

                    # 3. Wait for all 4 services to be healthy (up to 90s)
                    echo "Waiting for application services to become healthy..."
                    MAX_WAIT=90
                    ELAPSED=0
                    ALL_HEALTHY=false
                    while [ $ELAPSED -lt $MAX_WAIT ]; do
                        HEALTHY=$(docker ps --filter "name=orderflow" --filter "health=healthy" -q | wc -l)
                        echo "  [${ELAPSED}s] Healthy containers: $HEALTHY / 4"
                        if [ "$HEALTHY" -ge 4 ]; then
                            ALL_HEALTHY=true
                            echo "All services healthy!"
                            break
                        fi
                        sleep 5
                        ELAPSED=$((ELAPSED + 5))
                    done

                    if [ "$ALL_HEALTHY" != "true" ]; then
                        echo "FAIL: Services did not become healthy within ${MAX_WAIT}s"
                        docker ps --filter "name=orderflow"
                        for SVC in orderflow-postgres orderflow-order orderflow-inventory orderflow-notification; do
                            echo "--- Logs for $SVC ---"
                            docker logs "$SVC" --tail 20 2>&1 || true
                        done
                        exit 1
                    fi

                    # 4. Run the integration test container on the same network
                    docker-compose \
                        -f docker-compose.yml \
                        -f docker-compose.test.yml \
                        run --rm integration-test
                    echo "=== All integration tests passed! ==="
                '''
            }
            post {
                always {
                    sh 'docker-compose -f docker-compose.yml -f docker-compose.test.yml down -v --remove-orphans || true'
                }
            }
        }
 
        stage('Push to ECR') {
            when {
                branch 'main'
            }
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'aws-credentials',
                        usernameVariable: 'AWS_ACCESS_KEY_ID',
                        passwordVariable: 'AWS_SECRET_ACCESS_KEY'
                    ),
                    string(credentialsId: 'ecr-registry-URL', variable: 'ECR_REGISTRY')
                ]) {
                    sh '''
                        echo "=== Authenticating with ECR ==="
                        aws ecr get-login-password --region ${AWS_REGION} \
                            | docker login --username AWS --password-stdin ${ECR_REGISTRY}

                        echo "=== Pushing images ==="
                        for svc in order-service inventory-service notification-service; do
                            echo "--- Pushing ${svc} ---"
                            docker tag ${PROJECT_NAME}/${svc}:${IMAGE_TAG} \
                                ${ECR_REGISTRY}/corso-devops-${svc}:${IMAGE_TAG}
                            docker tag ${PROJECT_NAME}/${svc}:latest \
                                ${ECR_REGISTRY}/corso-devops-${svc}:latest
                            docker push ${ECR_REGISTRY}/corso-devops-${svc}:${IMAGE_TAG}
                            docker push ${ECR_REGISTRY}/corso-devops-${svc}:latest
                            echo "${svc} pushed successfully"
                        done

                        echo "=== All images pushed to ECR ==="
                    '''
                }
            }
        }

        // === STAGE NUOVO NEL GIORNO 3 ===
        // Verifica che le immagini pushate siano effettivamente presenti su ECR
        stage('Verify ECR') {
            when {
                branch 'main'
            }
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'aws-credentials',
                        usernameVariable: 'AWS_ACCESS_KEY_ID',
                        passwordVariable: 'AWS_SECRET_ACCESS_KEY'
                    ),
                    string(credentialsId: 'ecr-registry-URL', variable: 'ECR_REGISTRY')
                ]) {
                    sh '''
                        echo "=== Verifying images in ECR ==="
                        for svc in order-service inventory-service notification-service; do
                            MANIFEST=$(aws ecr batch-get-image \
                                --repository-name ${svc} \
                                --image-ids imageTag=${IMAGE_TAG} \
                                --query 'images[0].imageManifest' \
                                --output text --region ${AWS_REGION} 2>/dev/null)
                            if [ -z "$MANIFEST" ] || [ "$MANIFEST" = "None" ]; then
                                echo "FAIL: ${svc}:${IMAGE_TAG} not found in ECR"
                                exit 1
                            fi
                            echo "PASS: ${svc}:${IMAGE_TAG} verified in ECR"
                        done
                        echo "=== ECR verification passed ==="
                    '''
                }
            }
        }
    }

    // === POST BLOCK EVOLUTO DAL GIORNO 2 ===
    // Giorno 2 aveva: success/failure echo + cleanup immagini + cleanWs()
    // Giorno 3 aggiunge: JUnit report parsing, artifact archiving, cleanup migliorato
    post {
        success {
            echo """
            ====================================
            Pipeline SUCCESS - Build #${BUILD_NUMBER}
            Commit: ${GIT_SHORT_SHA}
            Tag: ${IMAGE_TAG}
            Services: order, inventory, notification
            ====================================
            """
        }

        failure {
            echo """
            ====================================
            Pipeline FAILED - Build #${BUILD_NUMBER}
            Commit: ${GIT_SHORT_SHA}
            Check stage logs for details.
            ====================================
            """
            // Uncomment for Slack notifications:
            // slackSend(channel: '#devops-alerts', color: 'danger',
            //     message: "OrderFlow Pipeline FAILED - Build #${BUILD_NUMBER} (${GIT_SHORT_SHA})")
        }

        always {
            // NUOVO: JUnit report parsing → visualizzazione test nella UI Jenkins
            sh '''
                echo "=== Test results directory ==="
                ls -la test-results/ 2>/dev/null || echo "test-results/ not found"
                chown -R $(id -u):$(id -g) test-results/ 2>/dev/null || true
            '''
            junit allowEmptyResults: true, testResults: 'test-results/*-results.xml'
            archiveArtifacts artifacts: 'test-results/*.log', allowEmptyArchive: true

            // Cleanup — evoluzione del Giorno 2 (che faceva solo docker rmi + cleanWs)
            sh '''
                echo "=== Final Cleanup ==="
                # Cleanup test containers from this build
                for SVC in order inventory notification; do
                    docker rm -f "test-${SVC}-${BUILD_NUMBER}" 2>/dev/null || true
                done
                # Cleanup compose containers and dangling images
                docker ps -aq --filter "name=orderflow" | xargs -r docker rm -f || true
                docker image prune -f --filter "until=2h" || true
            '''
        }
    }
}

 




